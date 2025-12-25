# Deprecated functionality - will be removed in future versions
from ..public.syntax import join_tickets, read_ticket, split_ticket


class Contract:
    def __init_subclass__(cls, **kwargs):
        raise ModuleNotFoundError(
            "`sp.Contract` can only be accessed within a .spy file or a function decorated with @sp.module. Please refer to the SmartPy documentation for more information."
        )


def read_ticket_raw(ticket):
    return read_ticket(ticket)


def split_ticket_raw(ticket, amounts):
    return split_ticket(ticket, amounts)


def join_tickets_raw(tickets):
    (ticket1, ticket2) = tickets
    return join_tickets(ticket1, ticket2)
