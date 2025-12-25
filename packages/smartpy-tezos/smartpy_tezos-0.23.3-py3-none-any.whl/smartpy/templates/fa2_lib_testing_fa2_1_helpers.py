import smartpy as sp


@sp.module
def helpers_fa2_1():
    t_ticket: type = sp.ticket[sp.pair[sp.nat, sp.option[sp.bytes]]]
    t_lambda_action: type = sp.lambda_(sp.list[t_ticket], sp.list[sp.operation])
    t_sandbox: type = sp.pair[sp.list[t_ticket], t_lambda_action]

    class Sandbox(sp.Contract):
        @sp.entrypoint
        def default(self, param):
            sp.cast(param, t_sandbox)
            (tickets, l) = param
            sp.operations = l(tickets)

    class Receiver(sp.Contract):
        def __init__(self):
            self.data.tickets = sp.big_map()
            self.data.id = 0

        @sp.entrypoint
        def default(self, param):
            sp.cast(param, t_ticket)
            with sp.modify_record(self.data) as data:
                data.tickets[data.id] = param
                data.id += 1

        @sp.entrypoint
        def check(self, checks):
            sp.cast(
                checks,
                sp.map[
                    sp.nat,
                    sp.record(
                        ticketer=sp.address,
                        amount=sp.nat,
                        contents=sp.pair[sp.nat, sp.option[sp.bytes]],
                    ),
                ],
            )
            with sp.modify_record(self.data) as data:
                for c in checks.items():
                    (el, tickets) = sp.get_and_update(c.key, None, data.tickets)
                    (ticket_data, copy) = sp.read_ticket(el.unwrap_some())
                    assert c.value.ticketer == ticket_data.ticketer
                    assert c.value.amount == ticket_data.amount
                    assert c.value.contents == ticket_data.contents
                    data.tickets = tickets
                    data.tickets[c.key] = copy

    class DestinationReceiver(sp.Contract):
        def __init__(self):
            self.data.received = sp.big_map()

        @sp.entrypoint
        def default(self, param):
            sp.cast(param, sp.list[sp.pair[sp.address, sp.list[t_ticket]]])
            with sp.modify_record(self.data) as data:
                data.received[0] = param

        @sp.entrypoint
        def check(self, batch):
            """
            A map of each element of data.received[0]
            associated to an incrementing nat number key.
            """
            sp.cast(
                batch,
                sp.map[
                    sp.nat,
                    sp.pair[
                        sp.address,
                        sp.map[
                            sp.nat,
                            sp.record(
                                ticketer=sp.address,
                                amount=sp.nat,
                                contents=sp.pair[sp.nat, sp.option[sp.bytes]],
                            ),
                        ],
                    ],
                ],
            )
            with sp.modify_record(self.data) as data:
                (received_option, bm_received) = sp.get_and_update(
                    0, None, data.received
                )
                data.received = bm_received
                match received_option:
                    case Some(received):
                        i = 0
                        new_received = []
                        for batch_received in received:
                            (to_, list_ticket) = batch_received
                            (check_to, check_tickets) = batch[i]
                            assert to_ == check_to
                            i += 1
                            j = 0
                            new_ticket_list = []
                            for ticket in list_ticket:
                                (ticket_data, copy) = sp.read_ticket(ticket)
                                assert check_tickets[j].ticketer == ticket_data.ticketer
                                assert check_tickets[j].amount == ticket_data.amount
                                assert check_tickets[j].contents == ticket_data.contents
                                j += 1
                                new_ticket_list.push(copy)
                            assert j == len(check_tickets)
                            new_received.push((to_, reversed(new_ticket_list)))
                        assert i == len(batch)
                        data.received[0] = reversed(new_received)

    class LambdaMaker(sp.Contract):
        @sp.onchain_view()
        def build_lambda(self, lambda_, to_):
            sp.cast(
                lambda_,
                sp.lambda_(
                    sp.pair[sp.address, sp.list[t_ticket]],
                    sp.list[sp.operation],
                ),
            )
            sp.cast(to_, sp.address)
            return lambda_.apply(to_)

    def lambda_export_ticket(param):
        (to_, tickets) = param
        sp.cast(tickets, sp.list[t_ticket])
        dest = sp.contract(t_ticket, to_).unwrap_some()
        operations = []
        first = True
        for ticket in tickets:
            if first:
                first = False
                operations.push(sp.transfer_operation(ticket, sp.amount, dest))
            else:
                operations.push(sp.transfer_operation(ticket, sp.tez(0), dest))
        return operations

    class AddressReceiver(sp.Contract):
        def __init__(self):
            self.data.x = None

        @sp.entrypoint
        def default(self, x):
            self.data.x = sp.Some(sp.cast(x, sp.address))

    def lambda_send_self_address(param):
        (to_, tickets) = param
        sp.cast(tickets, sp.list[t_ticket])
        dest = sp.contract(sp.address, to_).unwrap_some()
        operations = [sp.transfer_operation(sp.self_address, sp.tez(0), dest)]
        return operations
