let chart_data = [];
let dpi = window.devicePixelRatio;
const canvas = document.getElementById('chart');
const ctx = canvas.getContext('2d');
const container = $('#chart-container');
let height = 0;
let width = 0;
let maximal = 8050;
let minimal = 7900;
let chart_price_step = 200;
let mouse_x = null;
let mouse_y = null;
let is_dragging = false;
let drag_x = null;
let drag_y = null;
let position_start = 0;
let interval = '1m';
let vertical_scale = height;

const red_color = '#EA0070';
const green_color = '#46c345';
const buy_color = '#029900';
const sell_color = '#ff1600';

const candle_half_width = 4;
const candle_half_space = 6;

const right_panel_width = 70;

let candle_start = 0;
let max_candles = parseInt((width - right_panel_width) / (2 * candle_half_space + 1));


function reset_scale() {
    vertical_scale = height * 1.2;
    position_start = 0;
    candle_start = 0;
}

function fix_dpi() {
    let style_height = +getComputedStyle(canvas).getPropertyValue("height").slice(0, -2);
    let style_width = +getComputedStyle(canvas).getPropertyValue("width").slice(0, -2);
    canvas.setAttribute('height', style_height * dpi);
    canvas.setAttribute('width', style_width * dpi);
    height = style_height * dpi;
    width = style_width * dpi;
    ctx.font = "14px Consolas";
    max_candles = Math.max(0, parseInt((width - right_panel_width) / (2 * candle_half_space + 1)));
    reset_scale();
}

fix_dpi();

function price_to_y(price) {
    return parseInt(height - (parseFloat(price) - minimal) / (maximal - minimal) * height)
}

function y_to_price(y) {
    return ((height - y) * (maximal - minimal) / height + minimal).toString();
}

$('canvas')
    .mousemove(function (e) {
        const rect = canvas.getBoundingClientRect();
        mouse_x = (e.clientX - rect.left) * dpi;
        mouse_y = (e.clientY - rect.top) * dpi;
        redraw();
        if (is_dragging) {
            if (mouse_x > width - right_panel_width && drag_x > width - right_panel_width) {
                vertical_scale += (mouse_y - drag_y);
            } else {
                position_start = Math.max(0, position_start + (mouse_x - drag_x));
            }
            vertical_scale = Math.max(height / 2, vertical_scale);
            vertical_scale = Math.min(height * 4, vertical_scale);
            candle_start = Math.max(0, parseInt(position_start / (2 * candle_half_space + 1)));
        }
        drag_x = mouse_x;
        drag_y = mouse_y;
    })
    .mousedown(function (e) {
        const rect = canvas.getBoundingClientRect();
        is_dragging = true;
        drag_x = (e.clientX - rect.left) * dpi;
        drag_y = (e.clientY - rect.top) * dpi;
    })
    .mouseup(function (e) {
        is_dragging = false;
    })
    .mouseleave(function (e) {
        mouse_x = null;
        mouse_y = null;
        is_dragging = false;
        redraw();
    });

window.onresize = function () {
    fix_dpi();
    redraw();
};

function draw_candle(open, high, low, close, position) {
    let x_left = position - candle_half_width;
    let x_right = position + candle_half_width;
    let y_open = price_to_y(open);
    let y_close = price_to_y(close);
    let y_low = price_to_y(low);
    let y_high = price_to_y(high);
    ctx.beginPath();
    if (parseFloat(open) > parseFloat(close)) {
        ctx.fillStyle = red_color;
        ctx.strokeStyle = red_color;
    } else {
        ctx.fillStyle = green_color;
        ctx.strokeStyle = green_color;
    }
    ctx.moveTo(x_left, y_open);
    ctx.lineTo(x_right, y_open);
    ctx.lineTo(x_right, y_close);
    ctx.lineTo(x_left, y_close);
    ctx.closePath();
    ctx.globalAlpha = 0.2;
    ctx.fill();
    ctx.globalAlpha = 1.0;
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(position, y_low);
    ctx.lineTo(position, Math.max(y_open, y_close));
    ctx.moveTo(position, Math.min(y_open, y_close));
    ctx.lineTo(position, y_high);
    ctx.stroke();
}

function get_global_high(data) {
    let start = data.length - 1 - candle_start;
    let index = -1;
    for (let i = start; i >= Math.max(0, start - max_candles); i--) {
        if (index === -1 || parseFloat(data[i][2]) > parseFloat(data[index][2])) {
            index = i;
        }
    }
    return index;
}

function get_global_low(data) {
    let start = data.length - 1 - candle_start;
    let index = -1;
    for (let i = start; i >= Math.max(0, start - max_candles); i--) {
        if (index === -1 || parseFloat(data[i][3]) < parseFloat(data[index][3])) {
            index = i;
        }
    }
    return index;
}

function draw_horizontal(y, color, dash = []) {
    ctx.setLineDash(dash);
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.moveTo(0, y);
    ctx.lineTo(width - right_panel_width, y);
    ctx.stroke();
    ctx.setLineDash([]);
}

function draw_vertical(x, color, dash = []) {
    ctx.setLineDash(dash);
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
    ctx.setLineDash([]);
}

function draw_price_rect(price, color, text_color) {
    const y = price_to_y(price) + 5;
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(8 + width - right_panel_width, y + 2);
    ctx.lineTo(width - 1, y + 2);
    ctx.lineTo(width - 1, y - 12);
    ctx.lineTo(8 + width - right_panel_width, y - 12);
    ctx.lineTo(2 + width - right_panel_width, y - 5);
    ctx.closePath();
    ctx.fillStyle = '#FFFFFF';
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = text_color;
    ctx.fillText(trim_price(price), 10 + width - right_panel_width, y);
}

function update_chart_price_step() {
    for (let step = 1000; ; step /= 10) {
        if ((maximal - minimal) / (step * 5) > 4) {
            chart_price_step = step * 5;
            break;
        }
        if ((maximal - minimal) / (step * 2) > 4) {
            chart_price_step = step * 2;
            break;
        }
        if ((maximal - minimal) / (step) > 4) {
            chart_price_step = step;
            break;
        }
    }
}

function update_maximal_minimal(data, max_i, min_i) {
    if (max_i !== -1 && min_i !== -1) {
        maximal = parseFloat(data[max_i][2]);
        minimal = parseFloat(data[min_i][3]);
        const spread = (maximal - minimal) / 2;
        let average = (maximal + minimal) / 2;
        minimal = average - spread * (vertical_scale / height);
        maximal = average + spread * (vertical_scale / height);
    }
}

function draw_chart(data, cur_price) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const minimal_index = get_global_low(data);
    const maximal_index = get_global_high(data);
    update_maximal_minimal(data, maximal_index, minimal_index);

    let position = width - candle_half_space - right_panel_width;

    if (mouse_x != null) {
        draw_vertical(mouse_x, '#555555', [4, 4]);
        draw_horizontal(mouse_y, '#555555', [4, 4]);
    }

    draw_horizontal(price_to_y(cur_price), '#AAAAAA', [4, 4]);

    let start = data.length - 1 - candle_start;

    for (let i = start; i >= Math.max(0, start - max_candles); i--) {
        draw_candle(data[i][1], data[i][2], data[i][3], data[i][4], position);

        let shift = (position > width / 2 ? -50 : 0);
        ctx.fillStyle = '#555555';

        if (i === maximal_index) {
            ctx.fillText(trim_price(data[i][2], position), position + shift, price_to_y(data[i][2]) - 2);
        }
        if (i === minimal_index) {
            ctx.fillText(trim_price(data[i][3], position), position + shift, price_to_y(data[i][3]) + 11);
        }

        position -= candle_half_space * 2 + 1;
        if (position + candle_half_width < 0) break;
    }

    update_chart_price_step();
    ctx.clearRect(width - right_panel_width, 0, width, height);
    draw_vertical(width - right_panel_width, '#555555');

    for (let i = parseInt(minimal / chart_price_step); i <= parseInt(maximal / chart_price_step); i++) {
        draw_horizontal(price_to_y(i * chart_price_step), '#E0E0E0', [4, 4]);
        draw_price_rect((i * chart_price_step).toString(), '#E0E0E0', '#E0E0E0');
    }

    draw_price_rect(cur_price, green_color, '#555555');
    draw_price_rect(y_to_price(mouse_y), red_color, '#555555');

    draw_orders(active_orders);
}

function draw_order_price(position, text, price, quantity, color) {
    const y = price_to_y(price);
    draw_price_rect(price, color, '#555555');
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(position     ,y-8);
    ctx.lineTo(position + quantity.length * 8 + 4,y-8);
    ctx.lineTo(position + quantity.length * 8 + 4,y+8);
    ctx.lineTo(position     ,y+8);
    ctx.closePath();
    ctx.stroke();
    ctx.fillStyle = '#FFFFFF';
    ctx.fill();
    ctx.fillStyle = '#555555';
    ctx.fillText(quantity, position+3, y+5);


    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(position     ,y-8);
    ctx.lineTo(position - text.length * 8 - 2,y-8);
    ctx.lineTo(position - text.length * 8 - 2,y+8);
    ctx.lineTo(position     ,y+8);
    ctx.closePath();
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(text, position - text.length * 8 - 1, y+5);

}

function draw_orders(orders) {
    orders.forEach(function (order) {
        if (order['order_description'].indexOf('[Limit]') !== -1) {
            const price = order['price'].slice(3, -2);
            const quantity = order['quantity'].slice(3, -2);
            const color = order['side'] == 'BUY' ? buy_color : sell_color;
            draw_horizontal(price_to_y(price), color, [4, 4]);
            draw_order_price(
                width - right_panel_width - 150,
                order['side'],
                price,
                quantity,
                color
            );
        }
        if (order['order_description'].indexOf('[Stop loss]') !== -1) {
            const price = order['place_trigger'].slice(order['place_trigger'].indexOf('\'')+1, -2);
            const quantity = order['quantity'].slice(3, -2);
            const color = order['side'] === 'BUY' ? buy_color : sell_color;
            draw_horizontal(price_to_y(price), color, [4, 4]);
            draw_order_price(width - right_panel_width - 150, 'STOP', price,quantity, color);
        }

    });
}

function draw_buy_marker(price, candle) {
    if (candle < candle_start) return;
    let position = width - candle_half_space - right_panel_width
        - (candle - candle_start) * (2 * candle_half_space + 1);
    ctx.fillStyle = buy_color;
    ctx.strokeStyle = buy_color;
    let y = price_to_y(price);
    ctx.beginPath();
    ctx.moveTo(position, y);
    ctx.lineTo(position - candle_half_space - 2, y + candle_half_space + 2);
    ctx.lineTo(position + candle_half_space + 2, y + candle_half_space + 2);
    ctx.closePath();
    ctx.stroke();
    ctx.fill();
}

function draw_sell_marker(price, candle) {
    if (candle < candle_start) return;
    let position = width - candle_half_space - right_panel_width
        - (candle - candle_start) * (2 * candle_half_space + 1);
    ctx.fillStyle = sell_color;
    ctx.strokeStyle = sell_color;
    let y = price_to_y(price);
    ctx.beginPath();
    ctx.moveTo(position, y);
    ctx.lineTo(position - candle_half_space - 2, y - candle_half_space - 2);
    ctx.lineTo(position + candle_half_space + 2, y - candle_half_space - 2);
    ctx.closePath();
    ctx.stroke();
    ctx.fill();
}

function redraw() {
    draw_chart(chart_data, chart_data[chart_data.length - 1][4]);
    /* draw_buy_marker('7760', 20);
     draw_buy_marker('7938', 5);
     draw_sell_marker('8060', 3);
     draw_sell_marker('7830', 33);*/
}

function update_chart_data() {
    $.get(
        '/klines_' + BASE + '_' + QUOTE + '_' + interval,
        function (data) {
            chart_data = JSON.parse(data);
            redraw();
        }
    );
}

function choose_interval(interval_) {
    $('#int' + interval).css('background-color', '#DDDDDD');
    $('#int' + interval_).css('background-color', '#ffa762');
    interval = interval_;
    update_chart_data();
}

choose_interval('1d');
setInterval(update_chart_data, 5000);
