let active_orders = [];
let active_orders_table = $('#active-orders');

function construct_order(order) {
    return '<tr>\n' +
        '<td>' + timeConverter(order['time']) + '</td>\n' +
        '<td>' + order['order_description'] + '</td>\n' +
        '<td>'+order['status']+'</td>\n' +
        '<td>'+timeConverter(order['last_update'])+'</td>\n' +
        '<td>'+trim_price(order['high_price'])+ ' ' + QUOTE + '</td>\n' +
        '<td>'+trim_price(order['low_price'])+ ' ' + QUOTE + '</td>\n' +
        '<td><div class="cancel-button" onclick="cancel_order(\''+order['_id']['$oid']+'\')">Cancel</div></td>\n' +
        '</tr>';
}

function cancel_order(id) {
    $.get(
        '/cancel_order',
        {
            "id": id
        },
        function(data) {
            console.log(data);
        }
    )
}

function reload_orders() {
    $.get(
        '/active_orders_' + BASE + '_' + QUOTE,
        function(data) {
            active_orders = data;
            active_orders_table.html('<tr><td>Time</td><td>Order</td><td>Status</td>' +
                '<td>Last update</td><td>High</td><td>Low</td><td></td></tr>')
            data.forEach(function(order){active_orders_table.append(construct_order(order))});
        }
    )
}

setInterval(reload_orders, 1000);