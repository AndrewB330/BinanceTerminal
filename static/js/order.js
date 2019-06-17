const OrderType = {
    Limit: 0,
    StopLoss: 1,
    TakeProfit: 2,
    TrailingTakeProfit: 3
};

const limit_label = $('#type-limit');
const stop_label = $('#type-stop-loss');
const trailing_label = $('#type-take-profit');
const trailing_stop_label = $('#type-trailing-take-profit');
const type_labels = [limit_label, stop_label, trailing_label, trailing_stop_label];

let current_order_type = OrderType.Limit;


function choose_order_type(order_type) {
    type_labels[current_order_type].removeClass('active');
    current_order_type = order_type;
    type_labels[current_order_type].addClass('active');

    if (current_order_type === OrderType.Limit) {
        $('.market-button').show();
        $('.price-label').text('Price:');
        $('.row.delta').hide();
        $('.buy-section .description').text('Standard buy order');
        $('.sell-section .description').text('Standard sell order');
    }
    if (current_order_type === OrderType.StopLoss) {
        $('.market-button').hide();
        $('.price-label').text('Stop price:');
        $('.row.delta').hide();
        $('.buy-section .description').text('Buy market if price rises above [stop price]');
        $('.sell-section .description').text('Sell market if price drops below [stop price]');
    }
    if (current_order_type === OrderType.TakeProfit) {
        $('.market-button').hide();
        $('.price-label').text('TP price:');
        $('.row.delta').hide();
        $('.buy-section .description').text('Buy market if price drops below [TP price]');
        $('.sell-section .description').text('Sell market if price rises above [TP price]');
    }
    if (current_order_type === OrderType.TrailingTakeProfit) {
        $('.market-button').hide();
        $('.price-label').text('TTP price:');
        $('.row.delta').show();
        $('.buy-section .description').text('Buy market if price rises higher than [delta] from last [low],' +
            ' and [low] is lower than [price]');
        $('.sell-section .description').text('Sell market if price drops lower than [delta] from last [high],' +
            ' and [high] is higher than [price]');
    }
}

function createOrder(side) {
    if (current_order_type === OrderType.Limit) {
        $.get(
            '/limit_order',
            {
                "symbol": BASE + QUOTE,
                "side": side,
                "price": side === 'BUY' ?
                    $('.buy-section input[name=price]').val() :
                    $('.sell-section input[name=price]').val(),
                "quantity": side === 'BUY' ?
                    $('.buy-section input[name=amount]').val() :
                    $('.sell-section input[name=amount]').val(),
            },
            function (data) {
                console.log(data);
            }
        )
    }
}

choose_order_type(OrderType.Limit);