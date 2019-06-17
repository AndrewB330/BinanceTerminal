let asks = [];
let bids = [];
const depth_container = $('#depth');

function create_li_element(type, price, amount, percent) {
    return '<li class="' + type + '">\n' +
        '<a class="price">' + trim_price(price) + '</a>' +
        '<a class="total">' + trim_quote_amount((parseFloat(amount) * parseFloat(price)).toString()) + '</a><' +
        'a class="amount">' + trim_base_amount(amount) + '</a>\n' +
        '<div class="filler" style="width:' + percent + '%"></div>\n' +
        '</li>';
}

function build_depth() {
    depth_container.html('');
    let maximal = 0;
    asks.forEach(c => maximal = Math.max(maximal, parseFloat(c[1])));
    bids.forEach(c => maximal = Math.max(maximal, parseFloat(c[1])));
    for (let i = asks.length - 1; i >= 0; i--) {
        depth_container.append(
            create_li_element('ask', asks[i][0], asks[i][1], 5 + parseInt(95 * Math.sqrt(asks[i][1] / maximal)))
        );
    }
    for (let i = 0; i < asks.length; i++) {
        depth_container.append(
            create_li_element('bid', bids[i][0], bids[i][1], 5 + parseInt(95 * Math.sqrt(bids[i][1] / maximal)))
        );
    }
    update_events();
}


function update_depth_data(callback = null) {
    $.get(
        '/depth_' + BASE + '_' + QUOTE,
        function (data) {
            data = JSON.parse(data);
            asks = data['asks'].slice(0, 15);
            bids = data['bids'].slice(0, 15);
            build_depth();
            if (callback != null)
                callback();
        }
    );
}

setInterval(update_depth_data, 2000);

function update_events() {
    $('.ask > .price').click(function (e) {
        $('.sell-section input.price').val(trim_price(e.currentTarget.innerHTML));
    });
    $('.bid > .price').click(function (e) {
        $('.buy-section input.price').val(trim_price(e.currentTarget.innerHTML));
    });
}
