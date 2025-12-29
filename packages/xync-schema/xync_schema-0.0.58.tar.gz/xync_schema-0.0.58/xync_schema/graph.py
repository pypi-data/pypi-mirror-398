from xync_schema.enums import OrderStatus, OrderAction

acts = (
    {  # buyer
        # 1
        OrderStatus.created: {
            OrderAction.buyer_cancel: OrderStatus.canceled,
            OrderAction.buyer_pay: OrderStatus.paid,
        },
        # 2
        OrderStatus.paid: {
            OrderAction.buyer_cancel: OrderStatus.canceled,
            OrderAction.buyer_appeal: OrderStatus.appealed_by_buyer,
        },
        # 5
        OrderStatus.appealed_by_seller: {
            OrderAction.buyer_cancel: OrderStatus.canceled,
            OrderAction.buyer_dispute_appeal_s: OrderStatus.appeal_disputed,
        },
        # 6
        OrderStatus.appealed_by_buyer: {
            OrderAction.buyer_cancel: OrderStatus.canceled,
        },
        # 7
        OrderStatus.appeal_disputed: {
            OrderAction.buyer_cancel: OrderStatus.canceled,
        },
    },
    {  # seller
        # 2
        OrderStatus.paid: {
            OrderAction.seller_confirm: OrderStatus.completed,
            OrderAction.seller_appeal: OrderStatus.appealed_by_seller,
        },
        # 5
        OrderStatus.appealed_by_seller: {
            OrderAction.seller_confirm: OrderStatus.completed,
        },
        # 6
        OrderStatus.appealed_by_buyer: {
            OrderAction.seller_dispute_appeal_b: OrderStatus.appeal_disputed,
            OrderAction.seller_confirm: OrderStatus.completed,
        },
        # 7
        OrderStatus.appeal_disputed: {
            OrderAction.seller_confirm: OrderStatus.completed,
        },
    },
)


waits: dict[OrderStatus, dict[OrderAction, OrderStatus]] = {
    # 1
    OrderStatus.created: {
        OrderAction.wait_for_cancel: OrderStatus.canceled,
    },
    # 5
    OrderStatus.appealed_by_seller: {
        OrderAction.wait_appeal_s: OrderStatus.canceled,
    },
    # 6
    OrderStatus.appealed_by_buyer: {
        OrderAction.wait_appeal_b: OrderStatus.completed,
    },
}
