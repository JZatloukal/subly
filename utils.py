"""
Utility funkce pro aplikaci Subly
Obsahuje pomocné funkce pro kategorizaci, validaci, logování a zpracování dat
"""

import re
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
from flask import request, jsonify, current_app
import pandas as pd

# Konfigurace logování
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_category(name):
    """Automatically detect category based on service name"""
    if not name:
        return "Ostatní"
    
    name_lower = name.lower()
    
    # Entertainment services
    entertainment_keywords = [
        "netflix", "hbo", "disney", "prime", "skyshowtime", "apple tv", "voyo", 
        "paramount", "mubi", "filmbox", "rakuten", "starz", "iqiyi", "canal", 
        "curiosity", "oneplay", "iprima", "dazn", "sky", "hbo max"
    ]
    
    # Music services
    music_keywords = [
        "spotify", "tidal", "deezer", "soundcloud", "apple music", "youtube music", 
        "amazon music", "shazam", "audioteka", "podimo", "napster", "qobuz", 
        "iheartradio", "boomplay", "saavn", "yandex music", "anghami", "kkbox", 
        "joox", "idagio", "youtube premium"
    ]
    
    # Storage services
    storage_keywords = [
        "icloud", "google one", "dropbox", "onedrive", "microsoft 365", "pcloud", 
        "mega", "box", "tresorit", "nextcloud", "sync", "spideroak", "yandex disk", 
        "koofr", "backblaze", "idrive", "zoolz", "degoo", "icedrive", "nordlocker"
    ]
    
    # AI services
    ai_keywords = [
        "chatgpt", "openai", "midjourney", "copilot", "claude", "grok", "gemini", 
        "perplexity", "lumio", "huggingchat", "pi", "llama", "poe", "magai", "deepseek"
    ]
    
    # Productivity services
    productivity_keywords = [
        "notion", "todoist", "evernote", "clickup", "asana", "trello", "slack", 
        "zoom", "figma", "miro", "canva", "grammarly", "monday", "airtable", 
        "basecamp", "wrike", "adobe"
    ]
    
    # Check categories
    if any(keyword in name_lower for keyword in entertainment_keywords):
        return "Zábava"
    elif any(keyword in name_lower for keyword in music_keywords):
        return "Hudba"
    elif any(keyword in name_lower for keyword in storage_keywords):
        return "Úložiště"
    elif any(keyword in name_lower for keyword in ai_keywords):
        return "AI"
    elif any(keyword in name_lower for keyword in productivity_keywords):
        return "Produktivita"
    else:
        return "Ostatní"

def format_service_name(name):
    """Format service name consistently"""
    if not name:
        return ""
    return name.strip().title()

def calculate_category_totals(subscriptions):
    """Calculate total costs by category (monthly amounts)"""
    category_totals = defaultdict(float)
    
    for subscription in subscriptions:
        if subscription.is_active:
            monthly_cost = subscription.calculate_monthly_cost()
            category_totals[subscription.category] += monthly_cost
    
    return dict(category_totals)

def _calculate_next_payment_from_date(start_date, billing_cycle):
    """Calculate next payment date from start date using same logic as Subscription.update_next_payment()"""
    from datetime import date
    from dateutil.relativedelta import relativedelta
    
    today = date.today()
    next_payment = None
    
    if billing_cycle == "měsíčně":
        # Najdi nejbližší budoucí měsíční platbu
        # Vypočítej správné datum v aktuálním měsíci
        # Pokud je start_date v budoucnosti, použij start_date
        if start_date > today:
            next_payment = start_date
        else:
            # Najdi první budoucí platbu v aktuálním měsíci
            import calendar
            
            # Zkontroluj, jestli aktuální měsíc má dostatek dní pro start_date.day
            last_day_of_month = calendar.monthrange(today.year, today.month)[1]
            
            if start_date.day <= last_day_of_month:
                # Měsíc má dostatek dní, použij start_date.day
                current_month_payment = today.replace(day=start_date.day)
            else:
                # Měsíc nemá dostatek dní, použij poslední den měsíce
                current_month_payment = today.replace(day=last_day_of_month)
            
            # Pokud je dnešní den větší než current_month_payment, použij příští měsíc
            if current_month_payment <= today:
                next_payment = current_month_payment + relativedelta(months=1)
            else:
                next_payment = current_month_payment
        
    elif billing_cycle == "ročně":
        # Najdi nejbližší budoucí roční platbu
        if start_date > today:
            # Pokud je start_date v budoucnosti, next_payment je start_date
            next_payment = start_date
        else:
            # Najdi první budoucí roční platbu
            next_payment = start_date.replace(year=start_date.year + 1)
            while next_payment < today:
                next_payment = next_payment.replace(year=next_payment.year + 1)
    
    return next_payment

def get_upcoming_payments(subscriptions, days=7):
    """Get subscriptions with payments due within specified days"""
    upcoming = []
    today = datetime.now().date()
    
    for subscription in subscriptions:
        if subscription.is_active and subscription.next_payment:
            days_until = (subscription.next_payment - today).days
            if 0 <= days_until <= days:
                upcoming.append({
                    'subscription': subscription,
                    'days_until': days_until,
                    'is_overdue': days_until < 0
                })
    
    # Sort by days until payment
    upcoming.sort(key=lambda x: x['days_until'])
    return upcoming

def process_bank_statement_upload(file_path):
    """Process uploaded bank statement file and return subscription data"""
    try:
        file_extension = file_path.lower().split('.')[-1]
        
        if file_extension == 'csv':
            return _process_csv_file(file_path)
        else:
            raise ValueError(f"Nepodporovaný formát souboru: {file_extension}. Podporujeme pouze CSV.")
        
    except Exception as e:
        logger.error(f"Chyba při zpracování souboru: {e}")
        raise ValueError(f"Nepodařilo se zpracovat soubor: {str(e)}")

def _process_csv_file(file_path):
    """Process CSV file and return subscription data"""
    try:
        df = pd.read_csv(file_path)
        
        # Detect CSV format based on available columns
        is_bank_statement = 'Popis' in df.columns and 'Částka' in df.columns
        is_subscription_format = 'Název' in df.columns and 'Cena' in df.columns
        
        if not is_bank_statement and not is_subscription_format:
            raise ValueError("Nepodporovaný formát CSV. Očekáváme buď bankovní výpis (sloupce: Datum, Popis, Částka) nebo formát předplatných (sloupce: Název, Cena, Frekvence)")
        
        subscriptions = []
        
        if is_bank_statement:
            # Process bank statement format
            subscriptions = _process_bank_statement(df)
        else:
            # Process subscription format
            subscriptions = _process_subscription_format(df)
        
        return subscriptions
        
    except Exception as e:
        logger.error(f"Chyba při zpracování CSV: {e}")
        raise ValueError(f"Nepodařilo se zpracovat CSV soubor: {str(e)}")

def _process_xml_file(file_path):
    """Process XML bank statement file"""
    try:
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        transactions = []
        
        # Debug: print XML structure to understand the format
        all_elements = [elem.tag for elem in root.iter()]
        logger.info(f"XML structure: {all_elements[:20]}...")  # Show first 20 elements
        
        # Try to find transaction elements with various possible names
        transaction_elements = []
        possible_transaction_names = [
            'transaction', 'Transaction', 'TRANSACTION',
            'trans', 'Trans', 'TRANS',
            'movement', 'Movement', 'MOVEMENT',
            'operation', 'Operation', 'OPERATION',
            'entry', 'Entry', 'ENTRY',
            'record', 'Record', 'RECORD'
        ]
        
        for elem in root.iter():
            if elem.tag in possible_transaction_names:
                transaction_elements.append(elem)
                logger.info(f"Found transaction element: {elem.tag} with attributes: {elem.attrib}")
        
        logger.info(f"Found {len(transaction_elements)} transaction elements")
        
        # DEBUG: Check if we're processing all transactions
        logger.info(f"=== PROCESSING {len(transaction_elements)} TRANSACTIONS ===")
        
        # If no transaction elements found, try to find any element that might contain transaction data
        if not transaction_elements:
            # Look for elements that have multiple child elements (likely transaction records)
            for elem in root.iter():
                children = list(elem)
                if len(children) >= 3:  # At least 3 child elements (date, description, amount)
                    # Check if children have text content
                    text_children = [child for child in children if child.text and child.text.strip()]
                    if len(text_children) >= 3:
                        transaction_elements.append(elem)
                        logger.info(f"Found potential transaction element: {elem.tag} with {len(children)} children")
        
        # If still no transactions found, try a more aggressive approach
        if not transaction_elements:
            logger.info("No standard transaction elements found, trying aggressive search...")
            # Look for any element that might be a transaction based on content
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    # Check if this element contains what looks like transaction data
                    text = elem.text.strip()
                    # Look for patterns that suggest this might be transaction data
                    if (len(text) > 10 and 
                        (any(char.isdigit() for char in text)) and  # Contains numbers
                        (any(char.isalpha() for char in text))):    # Contains letters
                        # Check if parent has multiple children
                        parent = elem.getparent() if hasattr(elem, 'getparent') else None
                        if parent is not None:
                            siblings = list(parent)
                            if len(siblings) >= 3:
                                transaction_elements.append(parent)
                                logger.info(f"Found potential transaction parent: {parent.tag} with {len(siblings)} children")
                                break
        
        # Process found transaction elements
        for transaction in transaction_elements:
            try:
                # Try to find date, description, and amount elements with various possible names
                date_elem = None
                desc_elem = None
                amount_elem = None
                
                # Check if this is a MONETA Money Bank transaction (has attributes)
                if transaction.attrib:
                    # MONETA format: date-post, amount, trn-messages
                    date_text = transaction.attrib.get('date-post') or transaction.attrib.get('date-eff')
                    amount_text = transaction.attrib.get('amount')
                    
                    if date_text and amount_text:
                        # Find description in trn-messages
                        desc_text = ""
                        # Try to find the most relevant trn-message (usually the one with position="2" or the longest one)
                        trn_messages = transaction.findall('.//trn-message')
                        
                        if trn_messages:
                            # DEBUG: Show ALL trn-message texts for this transaction
                            logger.info(f"=== ALL TRN-MESSAGES FOR TRANSACTION {transaction.attrib.get('id', 'unknown')} ===")
                            for i, msg_elem in enumerate(trn_messages):
                                if msg_elem.text and msg_elem.text.strip():
                                    logger.info(f"  [{i}] position={msg_elem.attrib.get('position')}, text='{msg_elem.text.strip()}'")
                                else:
                                    logger.info(f"  [{i}] position={msg_elem.attrib.get('position')}, text='(empty)'")
                            logger.info("=== END TRN-MESSAGES ===")
                            
                            # Prefer position="2" if available, otherwise take the longest text
                            best_message = None
                            for msg_elem in trn_messages:
                                if msg_elem.text and msg_elem.text.strip():
                                    if msg_elem.attrib.get('position') == '2':
                                        best_message = msg_elem
                                        break
                                    elif not best_message or len(msg_elem.text.strip()) > len(best_message.text.strip()):
                                        best_message = msg_elem
                            
                            if best_message:
                                desc_text = best_message.text.strip()
                                logger.info(f"Selected description: {desc_text}")
                            else:
                                logger.warning("No valid trn-message found")
                        else:
                            logger.warning("No trn-message elements found")
                        
                        # If no trn-message found, use other-account-number as fallback
                        if not desc_text:
                            desc_text = transaction.attrib.get('other-account-number', 'Unknown transaction')
                        
                        if desc_text:
                            try:
                                amount_value = float(amount_text.replace(',', '.').replace(' ', ''))
                                transactions.append({
                                    'date': date_text,
                                    'description': desc_text,
                                    'amount': amount_value
                                })
                                logger.info(f"Processed MONETA transaction: {desc_text} - {amount_value}")
                                
                                # Debug: Check if this looks like a subscription
                                if any(service in desc_text.lower() for service in ['netflix', 'spotify', 'apple', 't-mobile']):
                                    logger.info(f"POTENTIAL SUBSCRIPTION FOUND: {desc_text}")
                                
                                continue
                            except ValueError as ve:
                                logger.warning(f"Invalid amount format: {amount_text} - {ve}")
                                continue
                
                # Standard approach for other banks
                # Possible field names for different banks
                date_names = ['date', 'Date', 'DATE', 'datum', 'Datum', 'DATUM', 'valueDate', 'ValueDate', 'VALUEDATE']
                desc_names = ['description', 'Description', 'DESCRIPTION', 'popis', 'Popis', 'POPIS', 'memo', 'Memo', 'MEMO', 'note', 'Note', 'NOTE', 'text', 'Text', 'TEXT']
                amount_names = ['amount', 'Amount', 'AMOUNT', 'castka', 'Castka', 'CASTKA', 'value', 'Value', 'VALUE', 'sum', 'Sum', 'SUM']
                
                # Find elements by name
                for child in transaction:
                    if child.tag in date_names:
                        date_elem = child
                    elif child.tag in desc_names:
                        desc_elem = child
                    elif child.tag in amount_names:
                        amount_elem = child
                
                # If not found by name, try to guess by position or content
                if not all([date_elem, desc_elem, amount_elem]):
                    children = list(transaction)
                    if len(children) >= 3:
                        # Try to identify by content patterns
                        for i, child in enumerate(children):
                            if child.text:
                                text = child.text.strip()
                                # Check if it looks like a date
                                if not date_elem and (len(text) >= 8 and any(char.isdigit() for char in text) and any(char in text for char in ['-', '/', '.'])):
                                    date_elem = child
                                # Check if it looks like an amount
                                elif not amount_elem and (text.replace(',', '.').replace(' ', '').replace('-', '').replace('+', '').replace('CZK', '').replace('Kč', '').replace('Kc', '').replace('EUR', '').replace('USD', '').replace(' ', '').replace('\xa0', '').isdigit() or (text.replace(',', '.').replace(' ', '').replace('-', '').replace('+', '').replace('CZK', '').replace('Kč', '').replace('Kc', '').replace('EUR', '').replace('USD', '').replace(' ', '').replace('\xa0', '') and '.' in text.replace(',', '.').replace(' ', '').replace('-', '').replace('+', '').replace('CZK', '').replace('Kč', '').replace('Kc', '').replace('EUR', '').replace('USD', '').replace(' ', '').replace('\xa0', ''))):
                                    amount_elem = child
                                # Everything else is likely description
                                elif not desc_elem and len(text) > 3:
                                    desc_elem = child
                
                if date_elem is not None and desc_elem is not None and amount_elem is not None:
                    # Clean and validate data
                    date_text = date_elem.text.strip() if date_elem.text else ""
                    desc_text = desc_elem.text.strip() if desc_elem.text else ""
                    amount_text = amount_elem.text.strip() if amount_elem.text else ""
                    
                    if date_text and desc_text and amount_text:
                        try:
                            # Clean amount text
                            amount_clean = amount_text.replace(',', '.').replace(' ', '').replace('CZK', '').replace('Kč', '').replace('Kc', '').replace('EUR', '').replace('USD', '').replace('\xa0', '')
                            amount_value = float(amount_clean)
                            
                            transactions.append({
                                'date': date_text,
                                'description': desc_text,
                                'amount': amount_value
                            })
                            logger.info(f"Processed transaction: {desc_text} - {amount_value}")
                        except ValueError as ve:
                            logger.warning(f"Invalid amount format: {amount_text} - {ve}")
                            continue
                else:
                    logger.warning(f"Missing required fields in transaction: date={date_elem is not None}, desc={desc_elem is not None}, amount={amount_elem is not None}")
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error processing transaction: {e}")
                continue
        
            logger.info(f"Successfully processed {len(transactions)} transactions")
            logger.info(f"=== FINAL RESULT: {len(transactions)} transactions processed from {len(transaction_elements)} found ===")
        
        if not transactions:
            # Debug: print XML structure to help identify the issue
            logger.error(f"XML structure: {all_elements}")
            logger.error(f"Found {len(transaction_elements)} transaction elements but processed 0 transactions")
            raise ValueError("Nepodařilo se najít transakce v XML souboru")
        
        # Convert to DataFrame and process like bank statement
        df = pd.DataFrame(transactions)
        df.columns = ['Datum', 'Popis', 'Částka']  # Standardize column names
        
        return _process_bank_statement(df)
        
    except Exception as e:
        logger.error(f"Chyba při zpracování XML: {e}")
        raise ValueError(f"Nepodařilo se zpracovat XML soubor: {str(e)}")

def _process_abo_file(file_path):
    """Process ABO format bank statement file"""
    try:
        # ABO format is typically a fixed-width format
        transactions = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
        
        for line in lines:
            line = line.strip()
            if len(line) < 20:  # Skip short lines
                continue
            
            try:
                # Common ABO format patterns
                # This is a simplified parser - real ABO formats can vary
                if '|' in line:
                    # Pipe-separated format
                    parts = line.split('|')
                    if len(parts) >= 3:
                        date_str = parts[0].strip()
                        description = parts[1].strip()
                        amount_str = parts[2].strip().replace(',', '.')
                        
                        transactions.append({
                            'date': date_str,
                            'description': description,
                            'amount': float(amount_str)
                        })
                elif '\t' in line:
                    # Tab-separated format
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        date_str = parts[0].strip()
                        description = parts[1].strip()
                        amount_str = parts[2].strip().replace(',', '.')
                        
                        transactions.append({
                            'date': date_str,
                            'description': description,
                            'amount': float(amount_str)
                        })
            except (ValueError, IndexError):
                continue
        
        if not transactions:
            raise ValueError("Nepodařilo se najít transakce v ABO souboru")
        
        # Convert to DataFrame and process like bank statement
        df = pd.DataFrame(transactions)
        df.columns = ['Datum', 'Popis', 'Částka']  # Standardize column names
        
        return _process_bank_statement(df)
        
    except Exception as e:
        logger.error(f"Chyba při zpracování ABO souboru: {e}")
        raise ValueError(f"Nepodařilo se zpracovat ABO soubor: {str(e)}")

def _process_txt_file(file_path):
    """Process TXT bank statement file"""
    try:
        # Try to read as CSV first
        try:
            df = pd.read_csv(file_path, sep='\t')  # Tab-separated
        except:
            try:
                df = pd.read_csv(file_path, sep=';')  # Semicolon-separated
            except:
                df = pd.read_csv(file_path, sep=',')  # Comma-separated
        
        # Check if it looks like a bank statement
        if 'Popis' in df.columns and 'Částka' in df.columns:
            return _process_bank_statement(df)
        elif 'Název' in df.columns and 'Cena' in df.columns:
            return _process_subscription_format(df)
        else:
            raise ValueError("Nepodporovaný formát TXT souboru")
        
    except Exception as e:
        logger.error(f"Chyba při zpracování TXT souboru: {e}")
        raise ValueError(f"Nepodařilo se zpracovat TXT soubor: {str(e)}")

def _process_bank_statement(df):
    """Process bank statement CSV format"""
    subscriptions = []
    
    # Group transactions by service name to detect recurring payments
    service_groups = {}
    
    for _, row in df.iterrows():
        try:
            description = str(row.get('Popis', '')).strip()
            amount = float(row.get('Částka', 0))
            date_str = str(row.get('Datum', ''))
            
            if not description or amount <= 0:
                continue
            
            # Extract service name from description
            service_name = _extract_service_name_from_description(description)
            if not service_name:
                continue
            
            # Parse date
            parsed_date = None
            if date_str:
                try:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            # Group by service name
            if service_name not in service_groups:
                service_groups[service_name] = []
            
            service_groups[service_name].append({
                'amount': amount,
                'date': parsed_date,
                'description': description
            })
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Chyba při zpracování řádku bankovního výpisu: {e}")
            continue
    
    # Process grouped services to detect subscriptions
    for service_name, transactions in service_groups.items():
        # For known subscription services, accept even single transactions
        known_subscription_services = [
            'netflix', 'spotify', 'youtube', 'apple', 'adobe', 'microsoft', 
            'disney', 'hbo', 'amazon', 'google', 'dropbox', 'icloud'
        ]
        
        is_known_service = any(known in service_name.lower() for known in known_subscription_services)
        
        if len(transactions) < 2 and not is_known_service:
            continue
        
        # Sort by date
        transactions.sort(key=lambda x: x['date'] if x['date'] else datetime.min.date())
        
        # Get most recent transaction
        latest_transaction = transactions[-1]
        amount = latest_transaction['amount']
        latest_date = latest_transaction['date']
        
        # Detect billing cycle based on transaction frequency
        billing_cycle = _detect_billing_cycle(transactions)
        
        # For known services with single transaction, assume monthly billing
        if len(transactions) == 1 and is_known_service:
            billing_cycle = "měsíčně"
        
        # Calculate next payment using start_date (first transaction), not latest_date
        next_payment = None
        start_date = transactions[0]['date'] if transactions else None
        if start_date and billing_cycle:
            next_payment = _calculate_next_payment_from_date(start_date, billing_cycle)
        
        subscriptions.append({
            'name': service_name,
            'price': amount,
            'billing_cycle': billing_cycle or 'měsíčně',
            'category': detect_category(service_name),
            'start_date': start_date,
            'next_payment': next_payment,
            'notes': f"Importováno z bankovního výpisu - {service_name}"
        })
    
    return subscriptions

def _process_subscription_format(df):
    """Process subscription CSV format"""
    subscriptions = []
    
    for _, row in df.iterrows():
        try:
            name = format_service_name(row.get('Název', ''))
            if not name:
                continue
            
            price = float(row.get('Cena', 0))
            if price <= 0:
                continue
            
            billing_cycle = row.get('Frekvence', 'měsíčně').lower()
            if billing_cycle not in ['měsíčně', 'ročně']:
                billing_cycle = 'měsíčně'
            
            category = detect_category(name)
            start_date = row.get('Začátek', '')
            
            # Parse start date
            parsed_start_date = None
            if start_date:
                try:
                    if isinstance(start_date, str):
                        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                    elif isinstance(start_date, pd.Timestamp):
                        parsed_start_date = start_date.date()
                except (ValueError, TypeError):
                    pass
            
            # Calculate next payment using proper logic
            next_payment = None
            if parsed_start_date:
                next_payment = _calculate_next_payment_from_date(parsed_start_date, billing_cycle)
            
            subscriptions.append({
                'name': name,
                'price': price,
                'billing_cycle': billing_cycle,
                'category': category,
                'start_date': parsed_start_date,
                'next_payment': next_payment,
                'notes': f"Importováno z CSV - {name}"
            })
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Chyba při zpracování řádku: {e}")
            continue
    
    return subscriptions

def _extract_service_name_from_description(description):
    """Extract service name from bank transaction description"""
    
    description_lower = description.lower()
    
    # WHITELIST - pouze ty nejznámější předplatné služby
    # Pokud transakce neobsahuje žádnou z těchto služeb, přeskočíme ji
    known_subscription_services = [
        # Streaming služby
        'netflix', 'spotify', 'youtube', 'hbo', 'amazon', 'apple tv', 'paramount', 'peacock', 'hulu', 'crunchyroll', 'twitch',
        # Hudební služby
        'apple music', 'amazon music', 'tidal', 'deezer', 'soundcloud',
        # Cloud a úložiště
        'google drive', 'onedrive', 'icloud', 'dropbox', 'box', 'pcloud',
        # Produktivita a software
        'microsoft', 'adobe', 'figma', 'notion', 'evernote', 'todoist',
        # Gaming
        'xbox', 'playstation', 'nintendo', 'steam', 'epic games',
        # Fitness a wellness
        'apple fitness', 'peloton', 'strava', 'myfitnesspal',
        # Apple služby (různé varianty)
        'apple.com', 'apple',
        # T-Mobile (různé varianty)
        't-mobile', 'tmobile', 't mobile'
    ]
    
    # Kontrola - pokud transakce neobsahuje žádnou známou službu, přeskočíme ji
    if not any(service in description_lower for service in known_subscription_services):
        # Debug: Log transactions that might be subscriptions but aren't in whitelist
        if any(keyword in description_lower for keyword in ['netflix', 'spotify', 'apple', 't-mobile', 'hbo', 'amazon']):
            logger.info(f"SKIPPED POTENTIAL SUBSCRIPTION: {description} (not in whitelist)")
        return None
    
    # Skip generic transaction descriptions that are not subscriptions
    generic_patterns = [
        r'^nákup\s+',
        r'^výběr\s+',
        r'^převod\s+',
        r'^inkaso\s+',
        r'^poplatek\s+',
        r'^úrok\s+',
        r'^splatba\s+',
        r'^příjem\s+',
        r'^vratka\s+',
        r'^storno\s+',
        r'^oprava\s+',
        r'^dobropis\s+',
        r'^úhrada\s+',
        r'^platba\s+za\s+',
        r'^zaplaceno\s+',
        r'^připsáno\s+',
        r'^odepsáno\s+',
    ]
    
    for pattern in generic_patterns:
        if re.match(pattern, description_lower):
            return None  # Skip generic transactions
    
    # Common patterns in bank descriptions for subscriptions
    patterns = [
        # Pattern for "Service Name - subscription type"
        r'([A-Za-z0-9\s]+?)\s*-\s*(?:měsíční|roční|předplatné|subscription)',
        # Pattern for "Service Name Premium/Standard/Family"
        r'([A-Za-z0-9\s]+?)\s+(?:Premium|Standard|Family|Pro|Plus)',
        # Pattern for "Service Name Cloud/Storage/Music/TV"
        r'([A-Za-z0-9\s]+?)\s+(?:Cloud|Storage|Music|TV)',
        # Pattern for "Service Name Creative/Office/365"
        r'([A-Za-z0-9\s]+?)\s+(?:Creative|Office|365)',
        # Pattern for "Disney+ Premium" type
        r'([A-Za-z0-9\s]+\+?)\s+(?:Premium|Standard|Family|Pro|Plus)',
        # Pattern for "Apple Music" type
        r'([A-Za-z0-9\s]+)\s+(?:Music|TV|News|Fitness)',
        # Pattern for "NETFLIX" or "Netflix" (case insensitive)
        r'(NETFLIX|Netflix|netflix)',
        # Pattern for "SPOTIFY" or "Spotify" (case insensitive)
        r'(SPOTIFY|Spotify|spotify)',
        # Pattern for "T-MOBILE" or "T-Mobile"
        r'(T-MOBILE|T-Mobile|T-MOBILE CZ)',
        # Pattern for "GOPAY" services
        r'(GOPAY\s+\*[A-Z0-9\.]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            service_name = match.group(1).strip()
            # Clean up the name
            service_name = re.sub(r'\s+', ' ', service_name)  # Multiple spaces to single
            service_name = service_name.title()  # Title case
            return service_name
    
    # Special handling for known services (matching whitelist)
    known_services = {
        # Streaming služby
        'netflix': 'Netflix',
        'spotify': 'Spotify Premium',
        'youtube': 'YouTube Premium',
        'hbo': 'HBO Max',
        'amazon': 'Amazon Prime',
        'apple tv': 'Apple TV+',
        'paramount': 'Paramount+',
        'peacock': 'Peacock',
        'hulu': 'Hulu',
        'crunchyroll': 'Crunchyroll',
        'twitch': 'Twitch Prime',
        # Hudební služby
        'apple music': 'Apple Music',
        'amazon music': 'Amazon Music',
        'tidal': 'Tidal',
        'deezer': 'Deezer',
        'soundcloud': 'SoundCloud Go',
        # Cloud a úložiště
        'google drive': 'Google Drive',
        'onedrive': 'OneDrive',
        'icloud': 'iCloud Storage',
        'dropbox': 'Dropbox',
        'box': 'Box',
        'pcloud': 'pCloud',
        # Produktivita a software
        'microsoft': 'Microsoft 365',
        'adobe': 'Adobe Creative Cloud',
        'figma': 'Figma',
        'notion': 'Notion',
        'evernote': 'Evernote',
        'todoist': 'Todoist',
        # Gaming
        'xbox': 'Xbox Game Pass',
        'playstation': 'PlayStation Plus',
        'nintendo': 'Nintendo Switch Online',
        'steam': 'Steam',
        'epic games': 'Epic Games',
        # Fitness a wellness
        'apple fitness': 'Apple Fitness+',
        'peloton': 'Peloton',
        'strava': 'Strava Premium',
        'myfitnesspal': 'MyFitnessPal Premium',
        # Apple služby (různé varianty)
        'apple.com': 'Apple Services',
        'apple': 'Apple Services',
        # T-Mobile (různé varianty)
        't-mobile': 'T-Mobile',
        'tmobile': 'T-Mobile',
        't mobile': 'T-Mobile'
    }
    
    # Check for known services first (highest priority)
    for key, value in known_services.items():
        if key in description_lower:
            return value
    
    # If no pattern matches, try to extract first meaningful words
    # But only if it looks like a subscription service
    words = description.split()
    if len(words) >= 2:
        # Take first 2-3 words that look like a service name
        service_words = []
        for word in words[:3]:
            if word.isalpha() and len(word) > 2:
                service_words.append(word)
            if len(service_words) >= 2:
                break
        
        if service_words:
            potential_service = ' '.join(service_words).title()
            # Additional check - skip if it looks like a generic transaction
            if not any(generic in potential_service.lower() for generic in ['platba', 'nákup', 'výběr', 'převod']):
                return potential_service
    
    return None

def _detect_billing_cycle(transactions):
    """Detect billing cycle based on transaction dates"""
    if len(transactions) < 2:
        return None
    
    # Sort by date
    sorted_transactions = sorted([t for t in transactions if t['date']], key=lambda x: x['date'])
    
    if len(sorted_transactions) < 2:
        return None
    
    # Calculate intervals between transactions
    intervals = []
    for i in range(1, len(sorted_transactions)):
        interval = (sorted_transactions[i]['date'] - sorted_transactions[i-1]['date']).days
        intervals.append(interval)
    
    if not intervals:
        return None
    
    # Calculate average interval
    avg_interval = sum(intervals) / len(intervals)
    
    # Determine billing cycle based on average interval
    if 25 <= avg_interval <= 35:  # Monthly
        return "měsíčně"
    elif 350 <= avg_interval <= 380:  # Yearly
        return "ročně"
    else:
        return "měsíčně"  # Default to monthly

def require_json(f):
    """Decorator to require JSON content type"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function

def handle_errors(f):
    """Decorator for error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return jsonify({'error': 'Došlo k neočekávané chybě'}), 500
    return decorated_function

def log_user_action(action, user_id=None, details=None):
    """Log user actions for audit trail"""
    try:
        from flask import request
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
    except RuntimeError:
        # Working outside of request context
        ip_address = None
        user_agent = None
    
    log_data = {
        'action': action,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat(),
        'ip_address': ip_address,
        'user_agent': user_agent,
        'details': details
    }
    logger.info(f"User action: {log_data}")

def validate_file_upload(file):
    """Validate uploaded file"""
    if not file:
        raise ValueError("Nebyl vybrán žádný soubor")
    
    if file.filename == '':
        raise ValueError("Soubor nemá název")
    
    # Check file extension
    allowed_extensions = ['.csv']
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise ValueError("Podporujeme pouze CSV soubory. Pro převod XML na CSV použijte online konvertor nebo Excel.")
    
    # Check file size (16MB limit)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 16 * 1024 * 1024:  # 16MB
        raise ValueError("Soubor je příliš velký (max 16MB)")
    
    return True

def generate_export_data(subscriptions):
    """Generate data for CSV export"""
    export_data = []
    
    for subscription in subscriptions:
        export_data.append({
            'Název': subscription.name,
            'Cena': subscription.price,
            'Frekvence': subscription.billing_cycle,
            'Kategorie': subscription.category,
            'Začátek': subscription.start_date.strftime('%Y-%m-%d') if subscription.start_date else '',
            'Další platba': subscription.next_payment.strftime('%Y-%m-%d') if subscription.next_payment else '',
            'Poznámky': subscription.notes or '',
            'Aktivní': 'Ano' if subscription.is_active else 'Ne'
        })
    
    return export_data

def get_service_letter(service_name):
    """Get first letter of service name for icon display"""
    if not service_name or not service_name.strip():
        return '?'
    
    # Get first letter and convert to uppercase
    first_letter = service_name.strip()[0].upper()
    
    # Handle special characters and numbers
    if not first_letter.isalpha():
        return '#'
    
    return first_letter

def get_category_letter(category):
    """Get first letter of category name for icon display"""
    if not category or not category.strip():
        return '?'
    
    # Get first letter and convert to uppercase
    first_letter = category.strip()[0].upper()
    
    # Handle special characters and numbers
    if not first_letter.isalpha():
        return '#'
    
    return first_letter

def get_statistics(subscriptions):
    """Calculate application statistics"""
    if not subscriptions:
        return {
            'total_subscriptions': 0,
            'active_subscriptions': 0,
            'monthly_total': 0,
            'yearly_total': 0,
            'categories': {},
            'upcoming_payments': 0
        }
    
    active_subscriptions = [s for s in subscriptions if s.is_active]
    
    monthly_total = sum(s.calculate_monthly_cost() for s in active_subscriptions)
    yearly_total = sum(s.calculate_yearly_cost() for s in active_subscriptions)
    
    categories = calculate_category_totals(active_subscriptions)
    upcoming_payments = len(get_upcoming_payments(active_subscriptions))
    
    return {
        'total_subscriptions': len(subscriptions),
        'active_subscriptions': len(active_subscriptions),
        'monthly_total': round(monthly_total, 2),
        'yearly_total': round(yearly_total, 2),
        'categories': categories,
        'upcoming_payments': upcoming_payments
    }

def update_all_next_payments():
    """Update next payment dates for all subscriptions"""
    from models import Subscription, db
    subscriptions = Subscription.query.all()
    updated_count = 0
    
    for subscription in subscriptions:
        if subscription.start_date:
            old_next_payment = subscription.next_payment
            subscription.update_next_payment()
            if subscription.next_payment != old_next_payment:
                updated_count += 1
                logger.info(f"Updated next payment for {subscription.name}: {old_next_payment} -> {subscription.next_payment}")
    
    if updated_count > 0:
        db.session.commit()
        logger.info(f"Updated {updated_count} subscription next payment dates")
    
    return updated_count
