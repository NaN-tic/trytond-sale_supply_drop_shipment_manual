# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pyson import Eval
from trytond.pool import PoolMeta
from trytond.model import fields

__all__ = ['SaleLine']


class SaleLine:
    __metaclass__ = PoolMeta
    __name__ = 'sale.line'
    supply_sale = fields.Boolean('Supply On Sale',
        states={
                # TODO invisible product type are not goods or assets
                'invisible': Eval('type') != 'line',
            },
        depends=['type', 'product'])
    drop_shipment = fields.Boolean('Drop Shipment',
        states={
                'invisible': ~Eval('supply_sale') | (Eval('type') != 'line'),
            },
        depends=['supply_sale', 'type'])

    def on_change_product(self):
        super(SaleLine, self).on_change_product()

        self.supply_sale = False
        if self.product:
            self.supply_sale = self.product.supply_on_sale

    def supply_on_sale(self):
        if self.supply_sale:
            return self.supply_sale
        return super(SaleLine, self).supply_on_sale()

    def get_purchase_request(self):
        request = super(SaleLine, self).get_purchase_request()
        if request and request.party and self.product \
                and self.product.type in ('goods', 'assets') and self.drop_shipment:
           request.customer = self.sale.party
           request.delivery_address = self.sale.shipment_address
        return request
