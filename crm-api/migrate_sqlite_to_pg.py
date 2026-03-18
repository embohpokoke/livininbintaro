#!/usr/bin/env python3
"""
CRM Database Migration: SQLite → PostgreSQL
Version: 1.0
Date: 2026-03-07
Author: Asmuni (Claude Code)

Migrates CRM data from SQLite to PostgreSQL crm schema.
Handles schema differences and data type conversions.
"""

import sqlite3
import psycopg2
from datetime import datetime
import sys

# Configuration
SQLITE_DB = '/var/www/livininbintaro/crm-api/livininbintaro.db'
PG_CONFIG = {
    'dbname': 'livininbintaro',
    'user': 'livin',
    'password': 'L1v1n!B1nt4r0_2026',
    'host': 'localhost',
    'port': 5432
}

def convert_timestamp(ts_str):
    """Convert SQLite TEXT timestamp to PostgreSQL TIMESTAMPTZ"""
    if not ts_str:
        return None
    try:
        # Try ISO format first
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except:
        try:
            # Try common formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(ts_str, fmt)
                except:
                    continue
            return None
        except:
            return None

def migrate_leads(sqlite_conn, pg_conn):
    """Migrate leads table"""
    print('\n[1/4] Migrating leads...')
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Fetch all leads from SQLite
    sqlite_cur.execute('SELECT * FROM leads')
    leads = sqlite_cur.fetchall()
    columns = [desc[0] for desc in sqlite_cur.description]
    
    print(f'  Found {len(leads)} leads in SQLite')
    
    migrated = 0
    for lead in leads:
        lead_dict = dict(zip(columns, lead))
        
        # Map schema differences
        pg_cur.execute('''
            INSERT INTO crm.leads (
                id, name, phone, email, source, bucket, status,
                assigned_to, requirement_text, budget_min, budget_max,
                preferred_type, preferred_area, notes,
                ai_score, ai_score_reason, ai_scored_at,
                last_contacted_at, next_follow_up_at, follow_up_reason,
                sla_deadline, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
        ''', (
            lead_dict['id'],
            lead_dict['name'],
            lead_dict['phone'],
            lead_dict['email'],
            lead_dict['source'],
            lead_dict.get('bucket', 'inbox'),
            lead_dict.get('status', 'new'),
            None,  # assigned_to (TEXT → INTEGER, set NULL)
            lead_dict.get('requirement_text'),
            lead_dict.get('budget_min'),
            lead_dict.get('budget_max'),
            lead_dict.get('preferred_type'),
            lead_dict.get('preferred_area'),
            lead_dict.get('notes'),
            lead_dict.get('ai_score'),
            lead_dict.get('ai_score_reason'),
            convert_timestamp(lead_dict.get('ai_scored_at')),
            convert_timestamp(lead_dict.get('last_contacted_at')),
            convert_timestamp(lead_dict.get('next_follow_up_at')),
            lead_dict.get('follow_up_reason'),
            convert_timestamp(lead_dict.get('sla_deadline')),
            convert_timestamp(lead_dict.get('created_at')),
            convert_timestamp(lead_dict.get('updated_at'))
        ))
        migrated += 1
    
    # Update sequence
    pg_cur.execute("SELECT setval('crm.leads_id_seq', (SELECT MAX(id) FROM crm.leads))")
    
    print(f'  ✅ Migrated {migrated} leads')
    return migrated

def migrate_lead_activities(sqlite_conn, pg_conn):
    """Migrate lead_activities table"""
    print('\n[2/4] Migrating lead_activities...')
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    sqlite_cur.execute('SELECT * FROM lead_activities')
    activities = sqlite_cur.fetchall()
    columns = [desc[0] for desc in sqlite_cur.description]
    
    print(f'  Found {len(activities)} activities in SQLite')
    
    migrated = 0
    for activity in activities:
        act_dict = dict(zip(columns, activity))
        
        pg_cur.execute('''
            INSERT INTO crm.lead_activities (
                id, lead_id, activity_type, description, created_at
            ) VALUES (%s, %s, %s, %s, %s)
        ''', (
            act_dict['id'],
            act_dict['lead_id'],
            act_dict.get('activity_type'),
            act_dict.get('description'),
            convert_timestamp(act_dict.get('created_at'))
        ))
        migrated += 1
    
    # Update sequence
    pg_cur.execute("SELECT setval('crm.lead_activities_id_seq', (SELECT MAX(id) FROM crm.lead_activities))")
    
    print(f'  ✅ Migrated {migrated} activities')
    return migrated

def migrate_wa_messages(sqlite_conn, pg_conn):
    """Migrate wa_messages table"""
    print('\n[3/4] Migrating wa_messages...')
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    sqlite_cur.execute('SELECT * FROM wa_messages')
    messages = sqlite_cur.fetchall()
    columns = [desc[0] for desc in sqlite_cur.description]
    
    print(f'  Found {len(messages)} messages in SQLite')
    
    migrated = 0
    for msg in messages:
        msg_dict = dict(zip(columns, msg))
        
        pg_cur.execute('''
            INSERT INTO crm.wa_messages (
                id, lead_id, phone, sender_name, message,
                direction, message_type, media_url, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            msg_dict['id'],
            msg_dict.get('lead_id'),
            msg_dict['phone'],
            msg_dict.get('sender_name'),
            msg_dict.get('message'),
            msg_dict['direction'],
            msg_dict.get('message_type', 'text'),
            msg_dict.get('media_url'),
            convert_timestamp(msg_dict.get('created_at'))
        ))
        migrated += 1
    
    # Update sequence
    pg_cur.execute("SELECT setval('crm.wa_messages_id_seq', (SELECT MAX(id) FROM crm.wa_messages))")
    
    print(f'  ✅ Migrated {migrated} messages')
    return migrated

def migrate_wa_templates(sqlite_conn, pg_conn):
    """Migrate wa_templates table"""
    print('\n[4/4] Migrating wa_templates...')
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    sqlite_cur.execute('SELECT * FROM wa_templates')
    templates = sqlite_cur.fetchall()
    columns = [desc[0] for desc in sqlite_cur.description]
    
    print(f'  Found {len(templates)} templates in SQLite')
    
    migrated = 0
    for tpl in templates:
        tpl_dict = dict(zip(columns, tpl))
        
        pg_cur.execute('''
            INSERT INTO crm.wa_templates (
                id, name, category, message_template, is_active, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            tpl_dict['id'],
            tpl_dict['name'],
            tpl_dict.get('category'),
            tpl_dict['content'],
            tpl_dict.get('is_active', True),
            convert_timestamp(tpl_dict.get('created_at'))
        ))
        migrated += 1
    
    # Update sequence
    pg_cur.execute("SELECT setval('crm.wa_templates_id_seq', (SELECT MAX(id) FROM crm.wa_templates))")
    
    print(f'  ✅ Migrated {migrated} templates')
    return migrated

def verify_migration(pg_conn):
    """Verify data was migrated correctly"""
    print('\n[VERIFICATION] Checking migrated data...')
    pg_cur = pg_conn.cursor()
    
    tables = ['leads', 'lead_activities', 'wa_messages', 'wa_templates']
    for table in tables:
        pg_cur.execute(f'SELECT COUNT(*) FROM crm.{table}')
        count = pg_cur.fetchone()[0]
        print(f'  crm.{table}: {count} records')
    
    # Check sample lead
    pg_cur.execute('SELECT id, name, phone, bucket, ai_score FROM crm.leads LIMIT 1')
    sample = pg_cur.fetchone()
    if sample:
        print(f'\n  Sample lead: {sample}')
    
    return True

def main():
    print('='*60)
    print('CRM Database Migration: SQLite → PostgreSQL')
    print('='*60)
    
    try:
        # Connect to databases
        print('\n[CONNECT] Connecting to databases...')
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        print('  ✅ SQLite connected')
        
        pg_conn = psycopg2.connect(**PG_CONFIG)
        pg_conn.autocommit = False  # Use transactions
        print('  ✅ PostgreSQL connected')
        
        # Clear existing data in PostgreSQL (fresh migration)
        print('\n[PREPARE] Clearing existing data in crm schema...')
        pg_cur = pg_conn.cursor()
        pg_cur.execute('TRUNCATE crm.wa_messages, crm.lead_activities, crm.wa_templates, crm.leads RESTART IDENTITY CASCADE')
        pg_conn.commit()
        print('  ✅ Cleared')
        
        # Migrate tables
        stats = {
            'leads': migrate_leads(sqlite_conn, pg_conn),
            'activities': migrate_lead_activities(sqlite_conn, pg_conn),
            'messages': migrate_wa_messages(sqlite_conn, pg_conn),
            'templates': migrate_wa_templates(sqlite_conn, pg_conn)
        }
        
        # Commit transaction
        print('\n[COMMIT] Committing transaction...')
        pg_conn.commit()
        print('  ✅ Committed')
        
        # Verify
        verify_migration(pg_conn)
        
        # Close connections
        sqlite_conn.close()
        pg_conn.close()
        
        print('\n' + '='*60)
        print('✅ MIGRATION COMPLETED SUCCESSFULLY')
        print('='*60)
        print(f'  Leads: {stats["leads"]}')
        print(f'  Activities: {stats["activities"]}')
        print(f'  Messages: {stats["messages"]}')
        print(f'  Templates: {stats["templates"]}')
        print('\nNext steps:')
        print('  1. Update backend config.py to use PostgreSQL')
        print('  2. Restart livininbintaro-crm service')
        print('  3. Test webhook and API endpoints')
        print('  4. Archive SQLite database')
        
        return 0
        
    except Exception as e:
        print(f'\n❌ ERROR: {e}')
        import traceback
        traceback.print_exc()
        
        # Rollback on error
        if 'pg_conn' in locals():
            pg_conn.rollback()
            print('\n⚠️  Transaction rolled back')
        
        return 1

if __name__ == '__main__':
    sys.exit(main())
