"""Connection Type table creation and data population

Revision ID: 011
Revises: 010
Create Date: 2025-12-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text
import json

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None

# Connection type data to insert
CONNECTION_TYPES = {
    "athena": {
        "displayName": "Amazon Athena",
        "fields": [
            {"displayName": "AWS Access Key ID", "dbMapping": "login", "required": True, "type": "string", "maxLength": None},
            {"displayName": "AWS Secret Access Key", "dbMapping": "password", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Schema", "dbMapping": "schema", "required": False, "type": "string", "maxLength": 500},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    },
    "chime": {
        "displayName": "Amazon Chime Webhook",
        "fields": [
            {"displayName": "Chime Webhook Endpoint", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Chime Webhook token", "dbMapping": "password", "required": False, "type": "string", "maxLength": 500},
            {"displayName": "Schema", "dbMapping": "schema", "required": False, "type": "string", "maxLength": 500},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    },
    "emr": {
        "displayName": "Amazon Elastic Map Reduce (EMR)",
        "fields": [
            {"displayName": "Run Job Flow Configuration", "dbMapping": "extra", "required": True, "type": "json", "maxLength": None}
        ]
    },
    "redshift": {
        "displayName": "Amazon Redshift",
        "fields": [
            {"displayName": "Host", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Database", "dbMapping": "schema", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "User", "dbMapping": "login", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Password", "dbMapping": "password", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Port", "dbMapping": "port", "required": True, "type": "number", "maxLength": None},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    },
    "aws": {
        "displayName": "Amazon Web Services (AWS)",
        "fields": [
            {"displayName": "AWS Access Key ID", "dbMapping": "login", "required": True, "type": "string", "maxLength": None},
            {"displayName": "AWS Secret Access Key", "dbMapping": "password", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    },
    "email": {
        "displayName": "Email",
        "fields": [
            {"displayName": "Host", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Schema", "dbMapping": "schema", "required": False, "type": "string", "maxLength": 500},
            {"displayName": "Login", "dbMapping": "login", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Password", "dbMapping": "password", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Port", "dbMapping": "port", "required": True, "type": "number", "maxLength": None},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    },
    "ftp": {
        "displayName": "FTP",
        "fields": [
            {"displayName": "Host", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Schema", "dbMapping": "schema", "required": False, "type": "string", "maxLength": 500},
            {"displayName": "Login", "dbMapping": "login", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Password", "dbMapping": "password", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Port", "dbMapping": "port", "required": False, "type": "number", "maxLength": None},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    },
    "fs": {
        "displayName": "File(Path)",
        "fields": [
            {"displayName": "Path", "dbMapping": "extra.path", "required": True, "type": "string", "maxLength": None}
        ]
    },
    "generic": {
        "displayName": "Generic",
        "fields": [
            {"displayName": "Host", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Schema", "dbMapping": "schema", "required": False, "type": "string", "maxLength": 500},
            {"displayName": "Login", "dbMapping": "login", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Password", "dbMapping": "password", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Port", "dbMapping": "port", "required": False, "type": "number", "maxLength": None},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    },
    "http": {
        "displayName": "HTTP",
        "fields": [
            {"displayName": "Host", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Schema", "dbMapping": "schema", "required": False, "type": "string", "maxLength": 500},
            {"displayName": "Login", "dbMapping": "login", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Password", "dbMapping": "password", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Port", "dbMapping": "port", "required": False, "type": "number", "maxLength": None},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    },
    "imap": {
        "displayName": "IMAP",
        "fields": [
            {"displayName": "Host", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Schema", "dbMapping": "schema", "required": False, "type": "string", "maxLength": 500},
            {"displayName": "Login", "dbMapping": "login", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Password", "dbMapping": "password", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Port", "dbMapping": "port", "required": False, "type": "number", "maxLength": None},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    },
    "kubernetes": {
        "displayName": "Kubernetes Cluster Connection",
        "fields": [
            {"displayName": "In Cluster", "dbMapping": "extra.in_cluster", "required": False, "type": "boolean", "maxLength": None},
            {"displayName": "Kube Config Path", "dbMapping": "extra.kube_config_path", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Kube Config (JSON FORMAT)", "dbMapping": "extra.kube_config", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Namespace", "dbMapping": "extra.namespace", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Cluster Context", "dbMapping": "extra.cluster_context", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Disable Verify SSL", "dbMapping": "extra.disable_verify_ssl", "required": False, "type": "boolean", "maxLength": None},
            {"displayName": "Disable TCP Keepalive", "dbMapping": "extra.disable_tcp_keepalive", "required": False, "type": "boolean", "maxLength": None},
            {"displayName": "XCom Sidecar Image", "dbMapping": "extra.xcom_sidecar_container_image", "required": False, "type": "string", "maxLength": None},
            {"displayName": "XCom Sidecar Resources (JSON FORMAT)", "dbMapping": "extra.xcom_sidecar_container_resources", "required": False, "type": "string", "maxLength": None}
        ]
    },
    "package_index": {
        "displayName": "Package Index (Python)",
        "fields": [
            {"displayName": "Package Index URL", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Login", "dbMapping": "login", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Password", "dbMapping": "password", "required": False, "type": "string", "maxLength": None}
        ]
    },
    "postgres": {
        "displayName": "PostgreSQL",
        "fields": [
            {"displayName": "Host", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Database", "dbMapping": "schema", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Login", "dbMapping": "login", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Password", "dbMapping": "password", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Port", "dbMapping": "port", "required": True, "type": "number", "maxLength": None},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    },
    "smtp": {
        "displayName": "SMTP",
        "fields": [
            {"displayName": "Host", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Login", "dbMapping": "login", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Password", "dbMapping": "password", "required": True, "type": "string", "maxLength": None},
            {"displayName": "Port", "dbMapping": "port", "required": True, "type": "number", "maxLength": None},
            {"displayName": "From Email", "dbMapping": "extra.from_email", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Timeout", "dbMapping": "extra.timeout", "required": False, "type": "number", "maxLength": None},
            {"displayName": "Retry Limit", "dbMapping": "extra.retry_limit", "required": False, "type": "number", "maxLength": None},
            {"displayName": "Disable TLS", "dbMapping": "extra.disable_tls", "required": False, "type": "boolean", "maxLength": None},
            {"displayName": "Disable SSL", "dbMapping": "extra.disable_ssl", "required": False, "type": "boolean", "maxLength": None}
        ]
    },
    "sqlite": {
        "displayName": "SQLite",
        "fields": [
            {"displayName": "Host", "dbMapping": "host", "required": True, "type": "string", "maxLength": 500},
            {"displayName": "Schema", "dbMapping": "schema", "required": False, "type": "string", "maxLength": 500},
            {"displayName": "Login", "dbMapping": "login", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Password", "dbMapping": "password", "required": False, "type": "string", "maxLength": None},
            {"displayName": "Port", "dbMapping": "port", "required": False, "type": "number", "maxLength": None},
            {"displayName": "Extras", "dbMapping": "extra", "required": False, "type": "json", "maxLength": None}
        ]
    }
}


def upgrade():
    # Create CONNECTION_TYPE table if it doesn't exist
    connection = op.get_bind()
    
    # Check if table exists
    result = connection.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'CONNECTION_TYPE'
        );
    """))
    table_exists = result.scalar()
    
    if not table_exists:
        op.create_table(
            'CONNECTION_TYPE',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('key', sa.String(), nullable=False, unique=True, index=True),
            sa.Column('data', JSONB(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
            sa.UniqueConstraint('key', name='uq_CONNECTION_TYPE_key')
        )
    
    # Insert connection types (skip if already exists)
    for key, data in CONNECTION_TYPES.items():
        # Check if key already exists
        result = connection.execute(
            text('SELECT 1 FROM "CONNECTION_TYPE" WHERE key = :key'),
            {"key": key}
        )
        if result.fetchone() is None:
            connection.execute(
                text('INSERT INTO "CONNECTION_TYPE" (key, data) VALUES (:key, :data)'),
                {"key": key, "data": json.dumps(data)}
            )


def downgrade():
    # Remove all inserted connection types
    connection = op.get_bind()
    
    for key in CONNECTION_TYPES.keys():
        connection.execute(
            text('DELETE FROM "CONNECTION_TYPE" WHERE key = :key'),
            {"key": key}
        )
    
    op.drop_table('CONNECTION_TYPE')
