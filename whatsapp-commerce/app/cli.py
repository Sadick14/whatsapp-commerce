import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.auth.models import User, BusinessMember
from app.businesses.models import Business
from app.products.models import ProductCategory, Product
from app.customers.models import Customer
from app.orders.models import Order, OrderItem
from app.payments.models import BusinessPaymentConfig, Payment
from app.whatsapp.models import BusinessWhatsAppAccount


def register_cli(app):

    @app.cli.command("init-db")
    @click.option("--drop", is_flag=True, help="Drop existing tables before creating.")
    @with_appcontext
    def init_db(drop):
        """Creates SQLite database and all schema tables."""
        if drop:
            click.echo("⚠️ Dropping existing tables...")
            db.drop_all()
        click.echo("🔨 Creating all database tables...")
        db.create_all()
        click.echo("✅ Database schema created successfully at instance/app.db!")

    @app.cli.command("seed-owner")
    @click.option("--email", required=True)
    @click.option("--password", required=True)
    @click.option("--business", "business_name", required=True)
    @click.option("--slug", required=True)
    @with_appcontext
    def seed_owner(email, password, business_name, slug):
        """Seeds an owner user and business workspace."""
        if User.query.filter_by(email=email).first():
            click.echo("User exists.")
            return
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            full_name=email.split('@')[0]
        )
        db.session.add(user)
        db.session.flush()
        biz = Business(name=business_name, slug=slug, owner_id=user.id)
        db.session.add(biz)
        db.session.flush()
        db.session.add(BusinessMember(business_id=biz.id, user_id=user.id, role='OWNER'))
        db.session.commit()
        click.echo(f"✅ {email} → {business_name} ({biz.id})")

    @app.cli.command("seed-demo")
    @with_appcontext
    def seed_demo():
        """Seeds demo multi-tenant data: Sadick Sneakers and Ama Beauty."""
        db.create_all()

        # 1. Owner Sadick
        if not User.query.filter_by(email="sadick@sneakers.com").first():
            u1 = User(
                email="sadick@sneakers.com",
                password_hash=generate_password_hash("Password123!"),
                full_name="Sadick Sneakerhead",
                phone="+233240000001"
            )
            db.session.add(u1)
            db.session.flush()

            biz1 = Business(
                name="Sadick Sneakers",
                slug="sadick-sneakers",
                owner_id=u1.id,
                currency="GHS",
                phone="+233241111111",
                email="info@sadicksneakers.com"
            )
            db.session.add(biz1)
            db.session.flush()
            db.session.add(BusinessMember(business_id=biz1.id, user_id=u1.id, role='OWNER'))

            # Products for Sadick
            cat1 = ProductCategory(business_id=biz1.id, name="Sneakers", slug="sneakers")
            db.session.add(cat1)
            db.session.flush()

            p1 = Product(
                business_id=biz1.id,
                category_id=cat1.id,
                name="Air Jordan 1 High OG",
                sku="AJ1-HIGH-01",
                price=650.00,
                stock_quantity=15,
                low_stock_threshold=3,
                status="ACTIVE"
            )
            p2 = Product(
                business_id=biz1.id,
                category_id=cat1.id,
                name="Nike Dunk Low Retro",
                sku="DUNK-LOW-02",
                price=480.00,
                stock_quantity=20,
                low_stock_threshold=5,
                status="ACTIVE"
            )
            db.session.add_all([p1, p2])

            # WhatsApp channel for Sadick
            waba1 = BusinessWhatsAppAccount(
                business_id=biz1.id,
                phone_number_id="PNID_SADICK_111",
                display_phone_number="+233241111111",
                waba_id="WABA_SADICK_111",
                status="CONNECTED"
            )
            db.session.add(waba1)

        # 2. Owner Ama
        if not User.query.filter_by(email="ama@beauty.com").first():
            u2 = User(
                email="ama@beauty.com",
                password_hash=generate_password_hash("Password123!"),
                full_name="Ama Glow",
                phone="+233240000002"
            )
            db.session.add(u2)
            db.session.flush()

            biz2 = Business(
                name="Ama Beauty",
                slug="ama-beauty",
                owner_id=u2.id,
                currency="GHS",
                phone="+233242222222",
                email="care@amabeauty.com"
            )
            db.session.add(biz2)
            db.session.flush()
            db.session.add(BusinessMember(business_id=biz2.id, user_id=u2.id, role='OWNER'))

            # Products for Ama
            cat2 = ProductCategory(business_id=biz2.id, name="Skincare", slug="skincare")
            db.session.add(cat2)
            db.session.flush()

            p3 = Product(
                business_id=biz2.id,
                category_id=cat2.id,
                name="Organic Raw Shea Butter 500g",
                sku="SHEA-500",
                price=75.00,
                stock_quantity=50,
                low_stock_threshold=10,
                status="ACTIVE"
            )
            p4 = Product(
                business_id=biz2.id,
                category_id=cat2.id,
                name="Glow Vitamin C Face Serum",
                sku="GLOW-VITC",
                price=140.00,
                stock_quantity=25,
                low_stock_threshold=5,
                status="ACTIVE"
            )
            db.session.add_all([p3, p4])

            # WhatsApp channel for Ama
            waba2 = BusinessWhatsAppAccount(
                business_id=biz2.id,
                phone_number_id="PNID_AMA_222",
                display_phone_number="+233242222222",
                waba_id="WABA_AMA_222",
                status="CONNECTED"
            )
            db.session.add(waba2)

        db.session.commit()
        click.echo("✅ Demo multi-tenant data seeded: Sadick Sneakers & Ama Beauty!")