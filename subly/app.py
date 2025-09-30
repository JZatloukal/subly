"""
Subly - Aplikace pro správu předplatných
Hlavní Flask aplikace s kompletní funkcionalitou pro správu uživatelských předplatných
"""

import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify, Response, flash
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from urllib.parse import quote
import csv
import json
from datetime import datetime, timedelta

# Import vlastních modulů
from config import config
from models import db, User, Subscription, validate_subscription_data, validate_user_data
from utils import (
    detect_category, format_service_name, calculate_category_totals, 
    get_upcoming_payments, process_bank_statement_upload, require_json, handle_errors,
    log_user_action, validate_file_upload, generate_export_data, get_statistics
)

# Konfigurace logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """
    Factory pattern pro vytvoření Flask aplikace
    Umožňuje snadné testování a konfiguraci pro různé prostředí
    """
    app = Flask(__name__)
    
    # Načtení konfigurace podle prostředí
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Inicializace rozšíření
    db.init_app(app)
    CORS(app)  # Povolení CORS pro API
    migrate = Migrate(app, db)  # Migrace databáze
    
    # Vytvoření adresáře pro uploady
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Authentication decorator
    def login_required(view):
        from functools import wraps
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for("login"))
            return view(**kwargs)
        return wrapped_view
    
    # Load user before each request
    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = db.session.get(User, user_id) if user_id else None
    
    # Inject user into templates
    @app.context_processor
    def inject_user():
        try:
            from flask import session
            user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
        except RuntimeError:
            # Working outside of request context
            user = None
        return dict(user=user)

    @app.context_processor
    def inject_icon_functions():
        """Make icon functions available in templates"""
        from utils import get_service_letter, get_category_letter
        return dict(
            get_service_letter=get_service_letter,
            get_category_letter=get_category_letter
        )
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Main dashboard route
    @app.route("/")
    def landing():
        """Landing page pro nepřihlášené uživatele"""
        if g.user:
            return redirect(url_for('index'))
        return render_template('landing.html')
    
    @app.route("/dashboard")
    @login_required
    def index():
        """Main dashboard with subscriptions overview"""
        # Get search query
        query = request.args.get("q", "").strip().lower()
        
        # Get user subscriptions
        subscriptions_query = Subscription.query.filter_by(user_id=g.user.id)
        
        if query:
            subscriptions_query = subscriptions_query.filter(
                Subscription.name.ilike(f"%{query}%")
            )
        
        subscriptions = subscriptions_query.order_by(Subscription.name).all()
        
        # Calculate statistics
        stats = get_statistics(subscriptions)
        
        # Get upcoming payments
        upcoming_payments = get_upcoming_payments(subscriptions)
        
        # Sort subscriptions by next payment for timeline
        subscriptions_sorted = sorted(
            subscriptions,
            key=lambda s: s.next_payment if s.next_payment else datetime.max.date()
        )
        
        log_user_action('dashboard_view', g.user.id, {'query': query})
        
        return render_template(
            "index.html",
            subscriptions=subscriptions,
            subscriptions_sorted=subscriptions_sorted,
            monthly_total=stats['monthly_total'],
            yearly_total=stats['yearly_total'],
            category_totals=stats['categories'],
            upcoming_payments=upcoming_payments,
            stats=stats
        )
    
    # Add subscription route
    @app.route("/add", methods=["POST"])
    @login_required
    def add_subscription():
        """Add new subscription"""
        try:
            # Validate input data
            data = {
                'name': request.form.get("name", "").strip(),
                'price': request.form.get("price"),
                'billing_cycle': request.form.get("billing_cycle", "").lower(),
                'category': request.form.get("category", "").strip(),
                'start_date': request.form.get("start_date"),
                'next_payment': request.form.get("next_payment"),
                'notes': request.form.get("notes", "").strip()
            }
            
            # Validate data
            errors = validate_subscription_data(data)
            if errors:
                for error in errors:
                    return redirect(url_for("index") + f"?flash={quote(error)}&type=error")
            
            # Format and process data
            name = format_service_name(data['name'])
            price = float(data['price'])
            billing_cycle = "měsíčně" if data['billing_cycle'] in ["monthly", "měsíčně"] else "ročně"
            category = data['category'] or detect_category(name)
            
            # Check for duplicate subscription
            existing = Subscription.query.filter_by(user_id=g.user.id, name=name).first()
            if existing:
                return redirect(url_for("index") + f"?flash={quote('Předplatné s tímto názvem již existuje')}&type=error")
            
            # Parse dates
            start_date = None
            next_payment = None
            
            if data['start_date']:
                try:
                    start_date = datetime.strptime(data['start_date'], "%Y-%m-%d").date()
                except ValueError:
                    return redirect(url_for("index") + f"?flash={quote('Neplatný formát data začátku')}&type=error")
            
            if data['next_payment']:
                try:
                    next_payment = datetime.strptime(data['next_payment'], "%Y-%m-%d").date()
                except ValueError:
                    return redirect(url_for("index") + f"?flash={quote('Neplatný formát data další platby')}&type=error")
            
            # Create subscription
            subscription = Subscription(
                name=name,
                price=price,
                billing_cycle=billing_cycle,
                category=category,
                start_date=start_date,
                next_payment=next_payment,
                notes=data['notes'],
                user_id=g.user.id
            )
            
            # Auto-calculate next payment if not provided
            if start_date and not next_payment:
                subscription.update_next_payment()
            
            db.session.add(subscription)
            db.session.commit()
            
            log_user_action('subscription_added', g.user.id, {'subscription_id': subscription.id, 'name': name})
            
            return redirect(url_for("index") + f"?flash={quote('Předplatné bylo úspěšně přidáno')}&type=success")
            
        except Exception as e:
            logger.error(f"Error adding subscription: {e}")
            db.session.rollback()
            return redirect(url_for("index") + f"?flash={quote('Chyba při přidávání předplatného')}&type=error")
        
        return redirect(url_for("index"))
    
    # Edit subscription route (AJAX)
    @app.route("/edit-subscription", methods=["POST"])
    @login_required
    def edit_subscription_ajax():
        """Edit existing subscription via AJAX"""
        try:
            subscription_id = request.form.get("id")
            if not subscription_id:
                return jsonify({"success": False, "message": "Chybí ID předplatného"})
            
            subscription = Subscription.query.filter_by(id=subscription_id, user_id=g.user.id).first_or_404()
            
            # Validate input data
            data = {
                'name': request.form.get("name", "").strip(),
                'price': request.form.get("price"),
                'billing_cycle': request.form.get("billing_cycle", "").lower(),
                'category': request.form.get("category", "").strip(),
                'start_date': request.form.get("start_date"),
                'notes': request.form.get("notes", "").strip()
            }
            
            # Validate data
            errors = validate_subscription_data(data)
            if errors:
                return jsonify({"success": False, "message": errors[0]})
            
            # Update subscription
            old_start_date = subscription.start_date
            old_billing_cycle = subscription.billing_cycle
            
            subscription.name = format_service_name(data['name'])
            subscription.price = float(data['price'])
            subscription.billing_cycle = "měsíčně" if data['billing_cycle'] in ["monthly", "měsíčně"] else "ročně"
            subscription.category = data['category'] or detect_category(subscription.name)
            subscription.notes = data['notes']
            
            # Parse start_date
            if data['start_date']:
                try:
                    subscription.start_date = datetime.strptime(data['start_date'], "%Y-%m-%d").date()
                except ValueError:
                    return jsonify({"success": False, "message": "Neplatný formát data začátku."})
            
            # Aktualizuj next_payment pokud se změnil start_date nebo billing_cycle
            if (old_start_date != subscription.start_date or old_billing_cycle != subscription.billing_cycle) and subscription.start_date:
                subscription.update_next_payment()
            
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
            
            
            log_user_action('subscription_edited', g.user.id, {'subscription_id': subscription.id})
            return jsonify({"success": True, "message": "Předplatné bylo úspěšně upraveno."})
            
        except Exception as e:
            logger.error(f"Error editing subscription: {e}")
            db.session.rollback()
            return jsonify({"success": False, "message": "Došlo k chybě při úpravě předplatného."})
    
    # Delete subscription route
    @app.route("/delete/<int:id>")
    @login_required
    def delete_subscription(id):
        """Delete subscription"""
        try:
            subscription = Subscription.query.filter_by(id=id, user_id=g.user.id).first_or_404()
            subscription_name = subscription.name
            
            db.session.delete(subscription)
            db.session.commit()
            
            log_user_action('subscription_deleted', g.user.id, {'subscription_id': id, 'name': subscription_name})
            
            return redirect(url_for("index") + f"?flash={quote('Předplatné bylo úspěšně smazáno')}&type=success")
            
        except Exception as e:
            logger.error(f"Error deleting subscription: {e}")
            db.session.rollback()
            return redirect(url_for("index") + f"?flash={quote('Chyba při mazání předplatného')}&type=error")
        
        return redirect(url_for("index"))
    
    # Bulk delete route
    @app.route("/delete_selected", methods=["POST"])
    @login_required
    @require_json
    @handle_errors
    def delete_selected():
        """Delete multiple subscriptions"""
        data = request.get_json()
        ids = data.get("ids", [])
        
        if not ids:
            return jsonify({"error": "Žádná ID nebyla poskytnuta"}), 400
        
        deleted_count = 0
        for sub_id in ids:
            subscription = Subscription.query.filter_by(id=sub_id, user_id=g.user.id).first()
            if subscription:
                db.session.delete(subscription)
                deleted_count += 1
        
        db.session.commit()
        
        log_user_action('bulk_delete', g.user.id, {'deleted_count': deleted_count, 'ids': ids})
        return jsonify({"message": f"Bylo smazáno {deleted_count} předplatných"}), 200
    
    # Upload bank statement route
    @app.route("/upload", methods=["POST"])
    @login_required
    def upload_bank_statement():
        """Upload and process bank statement file"""
        try:
            file = request.files.get("file")
            validate_file_upload(file)
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            
            # Process bank statement (CSV, XML, ABO, TXT)
            subscriptions_data = process_bank_statement_upload(filepath)
            
            # Clean up file
            os.remove(filepath)
            
            log_user_action('bank_statement_uploaded', g.user.id, {'filename': filename, 'records': len(subscriptions_data)})
            
            # Add success message to template context
            return render_template("upload_preview.html", 
                                 subscriptions=subscriptions_data,
                                 flash_message="Výpis byl úspěšně nahrán",
                                 flash_type="success")
            
        except Exception as e:
            logger.error(f"Error uploading bank statement: {e}")
            return redirect(url_for("index") + f"?flash={quote('Chyba při nahrávání souboru')}&type=error")
    
    # Confirm CSV upload route
    @app.route("/confirm_upload", methods=["POST"])
    @login_required
    def confirm_upload():
        """Confirm and save selected subscriptions from CSV"""
        try:
            raw_data = request.form.get("data")
            selected_indices = request.form.getlist("selected")
            
            if not raw_data:
                return redirect(url_for("index"))
            
            subscriptions_data = json.loads(raw_data)
            saved_count = 0
            
            for idx in selected_indices:
                try:
                    sub_data = subscriptions_data[int(idx)]
                    
                    # Check for duplicates
                    existing = Subscription.query.filter_by(user_id=g.user.id, name=sub_data["name"]).first()
                    if existing:
                        continue
                    
                    # Parse dates - handle both date objects and date strings
                    start_date = None
                    next_payment = None
                    
                    if sub_data.get("start_date"):
                        if isinstance(sub_data["start_date"], str):
                            # Handle date string from JSON serialization
                            try:
                                start_date = datetime.strptime(sub_data["start_date"], "%Y-%m-%d").date()
                            except ValueError:
                                # Try alternative format
                                try:
                                    start_date = datetime.strptime(sub_data["start_date"], "%a, %d %b %Y %H:%M:%S %Z").date()
                                except ValueError:
                                    pass
                        else:
                            start_date = sub_data["start_date"]
                    
                    if sub_data.get("next_payment"):
                        if isinstance(sub_data["next_payment"], str):
                            # Handle date string from JSON serialization
                            try:
                                next_payment = datetime.strptime(sub_data["next_payment"], "%Y-%m-%d").date()
                            except ValueError:
                                # Try alternative format
                                try:
                                    next_payment = datetime.strptime(sub_data["next_payment"], "%a, %d %b %Y %H:%M:%S %Z").date()
                                except ValueError:
                                    pass
                        else:
                            next_payment = sub_data["next_payment"]
                    
                    # Create subscription
                    subscription = Subscription(
                        name=sub_data["name"],
                        price=float(sub_data["price"]),
                        billing_cycle=sub_data["billing_cycle"],
                        category=sub_data["category"],
                        start_date=start_date,
                        next_payment=next_payment,
                        notes=sub_data.get("notes", ""),
                        user_id=g.user.id
                    )
                    
                    db.session.add(subscription)
                    saved_count += 1
                    
                except (IndexError, ValueError, KeyError) as e:
                    logger.warning(f"Error processing subscription data: {e}")
                    continue
            
            db.session.commit()
            
            log_user_action('csv_confirmed', g.user.id, {'saved_count': saved_count})
            
            if saved_count > 0:
                return redirect(url_for("index") + f"?flash={quote(f'Předplatná byla úspěšně importována ({saved_count} položek)')}&type=success")
            else:
                return redirect(url_for("index") + f"?flash={quote('Žádná nová předplatná nebyla importována')}&type=warning")
            
        except Exception as e:
            logger.error(f"Error confirming upload: {e}")
            db.session.rollback()
            return redirect(url_for("index") + f"?flash={quote('Chyba při importu předplatných')}&type=error")
        
        return redirect(url_for("index"))
    
    # Export route
    @app.route("/export")
    @login_required
    def export_csv():
        """Export subscriptions to CSV"""
        try:
            subscriptions = Subscription.query.filter_by(user_id=g.user.id).all()
            export_data = generate_export_data(subscriptions)
            
            # Create CSV response
            def generate_csv():
                if not export_data:
                    yield "Název,Cena,Frekvence,Kategorie,Začátek,Další platba,Poznámky,Aktivní\n"
                    return
                
                # Header
                yield ",".join(export_data[0].keys()) + "\n"
                
                # Data
                for row in export_data:
                    yield ",".join(f'"{str(value)}"' for value in row.values()) + "\n"
            
            log_user_action('csv_exported', g.user.id, {'record_count': len(export_data)})
            
            return Response(
                generate_csv(),
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=predplatne_export.csv"}
            )
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return redirect(url_for("index"))
    
    # Authentication routes
    @app.route("/register", methods=["GET", "POST"])
    def register():
        """User registration"""
        if request.method == "POST":
            try:
                # Validate input data
                data = {
                    'name': request.form.get("name", "").strip(),
                    'email': request.form.get("email", "").strip(),
                    'password': request.form.get("password", ""),
                    'confirm_password': request.form.get("confirm_password", "")
                }
                
                # Validate data
                errors = validate_user_data(data)
                if data['password'] != data['confirm_password']:
                    errors.append("Hesla se neshodují.")
                
                if errors:
                    for error in errors:
                        return redirect(url_for("register") + f"?flash={quote(error)}&type=error")
                
                # Check if user already exists
                if User.query.filter_by(email=data['email']).first():
                    return redirect(url_for("register") + f"?flash={quote('Uživatel s tímto emailem již existuje')}&type=error")
                
                # Create user
                user = User(
                    email=data['email'],
                    name=data['name'],
                    is_active=True
                )
                user.set_password(data['password'])
                
                db.session.add(user)
                db.session.commit()
                
                # Auto login
                session["user_id"] = user.id
                
                log_user_action('user_registered', user.id, {'email': data['email']})
                return redirect(url_for("index") + f"?flash={quote('Účet byl úspěšně vytvořen')}&type=success")
                
            except Exception as e:
                logger.error(f"Error during registration: {e}")
                db.session.rollback()
                return redirect(url_for("register") + f"?flash={quote('Chyba při vytváření účtu')}&type=error")
        
        return render_template("register.html")
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """User login"""
        if request.method == "POST":
            try:
                email = request.form.get("email", "").strip()
                password = request.form.get("password", "")
                
                user = User.query.filter_by(email=email, is_active=True).first()
                
                if user and user.check_password(password):
                    session["user_id"] = user.id
                    log_user_action('user_login', user.id, {'email': email})
                    return redirect(url_for("index") + f"?flash={quote('Přihlášení proběhlo úspěšně')}&type=success")
                else:
                    log_user_action('login_failed', None, {'email': email})
                    return redirect(url_for("login") + f"?flash={quote('Nesprávné přihlašovací údaje')}&type=error")
                    
            except Exception as e:
                logger.error(f"Error during login: {e}")
                return redirect(url_for("login") + f"?flash={quote('Chyba při přihlašování')}&type=error")
        
        return render_template("login.html")
    
    @app.route("/logout")
    def logout():
        """User logout"""
        if g.user:
            log_user_action('user_logout', g.user.id)
        session.clear()
        return redirect(url_for("login"))
    
    # Profile route
    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        """User profile management"""
        if request.method == "POST":
            try:
                name = request.form.get("name", "").strip()
                current_password = request.form.get("current_password", "")
                new_password = request.form.get("new_password", "")
                delete_account = request.form.get("delete_account")
                
                if delete_account:
                    # Delete user account
                    user_id = g.user.id
                    db.session.delete(g.user)
                    db.session.commit()
                    session.clear()
                    
                    log_user_action('account_deleted', user_id)
                    return redirect(url_for("register") + f"?flash={quote('Účet byl úspěšně smazán')}&type=success")
                
                changed = False
                
                # Update name
                if name and name != g.user.name:
                    g.user.name = name
                    changed = True
                
                # Update password
                if new_password:
                    if not current_password or not g.user.check_password(current_password):
                        return redirect(url_for("profile") + f"?flash={quote('Nesprávné současné heslo')}&type=error")
                    
                    # Validate new password
                    password_errors = validate_user_data({'password': new_password})
                    if password_errors:
                        for error in password_errors:
                            if 'heslo' in error.lower():
                                return redirect(url_for("profile") + f"?flash={quote(error)}&type=error")
                    
                    g.user.set_password(new_password)
                    changed = True
                
                if changed:
                    db.session.commit()
                    log_user_action('profile_updated', g.user.id)
                    return redirect(url_for("profile") + f"?flash={quote('Profil byl úspěšně aktualizován')}&type=success")
                
            except Exception as e:
                logger.error(f"Error updating profile: {e}")
                db.session.rollback()
                return redirect(url_for("profile") + f"?flash={quote('Chyba při aktualizaci profilu')}&type=error")
        
        return render_template("profile.html")
    
    # Auto-detect routes
    @app.route('/auto-detect', methods=['GET','POST'])
    @login_required
    def auto_detect():
        """Auto-detect subscriptions endpoint"""
        if request.method == 'GET':
            # Zobrazení informativní stránky o automatické detekci
            return render_template("auto_detect_form.html")

        # Mock data for demonstration (in real app, this would connect to APIs)
        detected = [
            {"name": "Spotify Premium", "price": 169, "billing_cycle": "měsíčně", "category": "Hudba"},
            {"name": "Netflix Standard", "price": 259, "billing_cycle": "měsíčně", "category": "Zábava"},
            {"name": "iCloud Storage", "price": 99, "billing_cycle": "měsíčně", "category": "Úložiště"},
            {"name": "YouTube Premium", "price": 199, "billing_cycle": "měsíčně", "category": "Zábava"},
            {"name": "Adobe Creative Cloud", "price": 599, "billing_cycle": "měsíčně", "category": "Produktivita"},
            {"name": "Microsoft 365", "price": 199, "billing_cycle": "měsíčně", "category": "Produktivita"},
            {"name": "Disney+", "price": 199, "billing_cycle": "měsíčně", "category": "Zábava"},
            {"name": "Apple Music", "price": 99, "billing_cycle": "měsíčně", "category": "Hudba"}
        ]
        session['detected_data'] = json.dumps(detected)
        return redirect(url_for('auto_detect_results'))

    @app.route('/auto-detect/results')
    @login_required
    def auto_detect_results():
        """Auto-detect results page"""
        data = session.pop('detected_data', None)
        if not data:
            return redirect(url_for("index"))

        try:
            detected = json.loads(data)
        except json.JSONDecodeError:
            return redirect(url_for("index"))

        # Encode detected items as JSON strings for the form
        detected_encoded = [json.dumps(item) for item in detected]
        return render_template("auto_detect_results.html", detected=detected, detected_encoded=detected_encoded)

    @app.route('/auto-detect/save', methods=['POST'])
    @login_required
    def confirm_detected():
        """Save selected detected subscriptions"""
        raw_data = request.form.getlist("selected_subs")

        if not raw_data:
            return redirect(url_for("index"))

        saved_count = 0
        for item in raw_data:
            try:
                sub = json.loads(item)
                
                # Check for duplicates
                existing = Subscription.query.filter_by(user_id=g.user.id, name=sub["name"]).first()
                if existing:
                    continue
                
                # Create subscription
                new_sub = Subscription(
                    name=sub["name"],
                    price=float(sub["price"]),
                    billing_cycle=sub["billing_cycle"],
                    category=sub["category"],
                    start_date=None,
                    next_payment=None,
                    notes="Z automatické detekce",
                    user_id=g.user.id
                )
                
                db.session.add(new_sub)
                saved_count += 1
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Error processing detected subscription: {e}")
                continue

        db.session.commit()
        
        log_user_action('auto_detect_saved', g.user.id, {'saved_count': saved_count})
        
        if saved_count > 0:
            return redirect(url_for("index") + f"?flash={quote(f'Automatická detekce dokončena - uloženo {saved_count} předplatných')}&type=success")
        else:
            return redirect(url_for("index") + f"?flash={quote('Automatická detekce dokončena - žádná předplatná nebyla uložena')}&type=info")

    # API routes for future mobile app
    @app.route("/api/subscriptions")
    @login_required
    @require_json
    def api_subscriptions():
        """API endpoint for subscriptions"""
        subscriptions = Subscription.query.filter_by(user_id=g.user.id).all()
        return jsonify([sub.to_dict() for sub in subscriptions])
    
    @app.route("/api/statistics")
    @login_required
    @require_json
    def api_statistics():
        """API endpoint for statistics"""
        subscriptions = Subscription.query.filter_by(user_id=g.user.id).all()
        stats = get_statistics(subscriptions)
        return jsonify(stats)
    
    @app.route('/update-payments')
    @login_required
    def update_payments():
        """Update all subscription next payment dates"""
        from utils import update_all_next_payments
        updated_count = update_all_next_payments()
        return redirect(url_for('index'))
    
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        logger.info("Database tables created/verified")
    
    # Run app
    app.run(
        debug=app.config['DEBUG'],
        host="0.0.0.0",
        port=int(os.environ.get('PORT', 2000))
    )
