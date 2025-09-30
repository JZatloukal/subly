"""
Databázové modely pro aplikaci Subly
Obsahuje modely User a Subscription s validačními funkcemi
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Inicializace SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    """Model uživatele pro autentifikaci a správu uživatelů"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to subscriptions
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password, password)
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'subscription_count': len(self.subscriptions)
        }
    
    def __repr__(self):
        return f'<User {self.email}>'

class Subscription(db.Model):
    """Subscription model for managing user subscriptions"""
    __tablename__ = 'subscription'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    billing_cycle = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=True)
    next_payment = db.Column(db.Date, nullable=True, index=True)
    notes = db.Column(db.Text, nullable=True)
    icon_filename = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_subscription_user_id'), nullable=False, index=True)
    
    def __init__(self, **kwargs):
        super(Subscription, self).__init__(**kwargs)
        # Auto-generate icon filename if not provided
        if not self.icon_filename and self.name:
            self.icon_filename = self._generate_icon_filename()
    
    def _generate_icon_filename(self):
        """Generate icon filename from subscription name"""
        if not self.name:
            return None
        # Remove special characters and convert to lowercase
        clean_name = re.sub(r'[^a-z0-9]+', '', self.name.lower())
        return f"{clean_name}.svg"
    
    def calculate_monthly_cost(self):
        """Calculate monthly cost based on billing cycle"""
        if self.billing_cycle == "měsíčně":
            return self.price
        elif self.billing_cycle == "ročně":
            return round(self.price / 12, 2)
        return self.price
    
    def calculate_yearly_cost(self):
        """Calculate yearly cost based on billing cycle"""
        if self.billing_cycle == "měsíčně":
            return self.price * 12
        elif self.billing_cycle == "ročně":
            return self.price
        return self.price
    
    def is_payment_due_soon(self, days=7):
        """Check if payment is due within specified days"""
        if not self.next_payment:
            return False
        today = datetime.now().date()
        days_until_payment = (self.next_payment - today).days
        return 0 <= days_until_payment <= days
    
    def update_next_payment(self):
        """Update next payment date based on billing cycle and start date"""
        if not self.start_date:
            return
        
        from datetime import date, timedelta
        
        today = date.today()
        next_payment = None
        
        if self.billing_cycle == "měsíčně":
            # Najdi nejbližší budoucí měsíční platbu
            from dateutil.relativedelta import relativedelta
            
            # Vypočítej správné datum v aktuálním měsíci
            # Pokud je start_date v budoucnosti, použij start_date
            if self.start_date > today:
                next_payment = self.start_date
            else:
                # Najdi první budoucí platbu v aktuálním měsíci
                import calendar
                
                # Zkontroluj, jestli aktuální měsíc má dostatek dní pro start_date.day
                last_day_of_month = calendar.monthrange(today.year, today.month)[1]
                
                if self.start_date.day <= last_day_of_month:
                    # Měsíc má dostatek dní, použij start_date.day
                    current_month_payment = today.replace(day=self.start_date.day)
                else:
                    # Měsíc nemá dostatek dní, použij poslední den měsíce
                    current_month_payment = today.replace(day=last_day_of_month)
                
                # Pokud je dnešní den větší než current_month_payment, použij příští měsíc
                if current_month_payment <= today:
                    next_payment = current_month_payment + relativedelta(months=1)
                else:
                    next_payment = current_month_payment
            
        elif self.billing_cycle == "ročně":
            # Najdi nejbližší budoucí roční platbu
            if self.start_date > today:
                # Pokud je start_date v budoucnosti, next_payment je start_date
                next_payment = self.start_date
            else:
                # Najdi první budoucí roční platbu
                next_payment = self.start_date.replace(year=self.start_date.year + 1)
                while next_payment < today:
                    next_payment = next_payment.replace(year=next_payment.year + 1)
        
        self.next_payment = next_payment
    
    def to_dict(self):
        """Convert subscription to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'billing_cycle': self.billing_cycle,
            'category': self.category,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'next_payment': self.next_payment.isoformat() if self.next_payment else None,
            'notes': self.notes,
            'icon_filename': self.icon_filename,
            'is_active': self.is_active,
            'monthly_cost': self.calculate_monthly_cost(),
            'yearly_cost': self.calculate_yearly_cost(),
            'payment_due_soon': self.is_payment_due_soon(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Subscription {self.name} - {self.price} Kč>'

# Validation functions
def validate_subscription_data(data):
    """Validate subscription data"""
    errors = []
    
    # Name validation
    if not data.get('name') or len(data['name'].strip()) < 2:
        errors.append('Název služby musí mít alespoň 2 znaky')
    
    # Price validation
    try:
        price = float(data.get('price', 0))
        if price <= 0:
            errors.append('Cena musí být větší než 0')
        if price > 100000:  # Reasonable upper limit
            errors.append('Cena je příliš vysoká')
    except (ValueError, TypeError):
        errors.append('Neplatná cena')
    
    # Billing cycle validation
    valid_cycles = ['měsíčně', 'ročně', 'monthly', 'yearly']
    if data.get('billing_cycle') not in valid_cycles:
        errors.append('Neplatný billing cyklus')
    
    # Category validation
    valid_categories = ['Zábava', 'Hudba', 'Úložiště', 'AI', 'Produktivita', 'Ostatní']
    if data.get('category') and data['category'] not in valid_categories:
        errors.append('Neplatná kategorie')
    
    return errors

def validate_user_data(data):
    """Validate user registration data"""
    errors = []
    
    # Email validation
    email = data.get('email', '').strip()
    if not email:
        errors.append('Email je povinný')
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append('Neplatný email formát')
    
    # Password validation
    password = data.get('password', '')
    if len(password) < 8:
        errors.append('Heslo musí mít alespoň 8 znaků')
    elif not re.search(r'[A-Z]', password):
        errors.append('Heslo musí obsahovat alespoň jedno velké písmeno')
    elif not re.search(r'[a-z]', password):
        errors.append('Heslo musí obsahovat alespoň jedno malé písmeno')
    elif not re.search(r'\d', password):
        errors.append('Heslo musí obsahovat alespoň jednu číslici')
    
    # Name validation
    name = data.get('name', '').strip()
    if name and len(name) < 2:
        errors.append('Jméno musí mít alespoň 2 znaky')
    
    return errors
