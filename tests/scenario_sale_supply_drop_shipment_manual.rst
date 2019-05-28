=========================================
Sale Supply Drop Shipment Manual Scenario
=========================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Install sale_supply, sale, purchase::

    >>> config = activate_modules(['sale_supply_drop_shipment_manual', 'sale',
    ...             'purchase'])

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create sale user::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> sale_user = User()
    >>> sale_user.name = 'Sale'
    >>> sale_user.login = 'sale'
    >>> sale_user.main_company = company
    >>> sale_group, = Group.find([('name', '=', 'Sales')])
    >>> sale_user.groups.append(sale_group)
    >>> sale_user.save()

Create purchase user::

    >>> purchase_user = User()
    >>> purchase_user.name = 'Purchase'
    >>> purchase_user.login = 'purchase'
    >>> purchase_user.main_company = company
    >>> purchase_group, = Group.find([('name', '=', 'Purchase')])
    >>> purchase_user.groups.append(purchase_group)
    >>> purchase_request_group, = Group.find(
    ...     [('name', '=', 'Purchase Request')])
    >>> purchase_user.groups.append(purchase_request_group)
    >>> purchase_user.save()

Create stock user::

    >>> stock_user = User()
    >>> stock_user.name = 'Stock'
    >>> stock_user.login = 'stock'
    >>> stock_user.main_company = company
    >>> stock_group, = Group.find([('name', '=', 'Stock')])
    >>> stock_force_group, = Group.find([
    ...     ('name', '=', 'Stock Force Assignment'),
    ...     ])
    >>> stock_user.groups.append(stock_group)
    >>> stock_user.groups.append(stock_force_group)
    >>> stock_user.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']

Create parties::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create tax::

    >>> tax = create_tax(Decimal('.10'))
    >>> tax.save()

Create account categories::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_expense = expense
    >>> account_category.account_revenue = revenue
    >>> account_category.save()

    >>> account_category_tax, = account_category.duplicate()
    >>> account_category_tax.customer_taxes.append(tax)
    >>> account_category_tax.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> ProductSupplier = Model.get('purchase.product_supplier')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('5')
    >>> template.account_category = account_category_tax
    >>> template.supply_on_sale = True
    >>> template.save()
    >>> product, = template.products
    >>> product_supplier = ProductSupplier()
    >>> product_supplier.product = template
    >>> product_supplier.party = supplier
    >>> product_supplier.drop_shipment = False
    >>> product_supplier.lead_time = datetime.timedelta(0)
    >>> product_supplier.save()

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Sale 250 products::

    >>> config.user = sale_user.id
    >>> Sale = Model.get('sale.sale')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> bool(sale_line.supply_sale)
    True
    >>> sale_line.quantity = 250
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.state
    'processing'
    >>> len(sale.shipments)
    1

Sale 50 products and drop shipment::

    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 50
    >>> sale_line.drop_shipment = True
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.state
    'processing'
    >>> sale.shipments
    []
    >>> sale.drop_shipments
    []
    >>> len(sale.moves)
    1

Create a Purchase from Purchase Request::

    >>> config.user = purchase_user.id
    >>> PurchaseRequest = Model.get('purchase.request')
    >>> Purchase = Model.get('purchase.purchase')

    >>> pr1, pr2 = PurchaseRequest.find([])
    >>> pr2.customer
    >>> pr1.customer == customer
    True

    >>> create_purchase = Wizard('purchase.request.create_purchase',[pr1])
    >>> purchase, = Purchase.find()
    >>> purchase.customer == customer
    True
    >>> purchase.payment_term = payment_term
    >>> purchase.click('quote')
    >>> purchase.click('confirm')
    >>> purchase.state
    'processing'

Check sale drop shipment::

    >>> config.user = sale_user.id
    >>> sale.reload()
    >>> sale.shipments
    []
    >>> len(sale.drop_shipments)
    1
