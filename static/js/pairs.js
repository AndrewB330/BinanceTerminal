const home = window.location.href.substring(0, window.location.href.lastIndexOf('/') + 1);

const QuoteGroup = {
    Active: 0,
    BTC: 1,
    BNB: 2,
    ALTS: 3,
    USD: 4
};

let current_quote_group = QuoteGroup.BTC;
const active_qg_label = $('#active-qg');
const btc_qg_label = $('#btc-qg');
const bnb_qg_label = $('#bnb-qg');
const alts_qg_label = $('#alts-qg');
const usd_qg_label = $('#usd-qg');

const qg_labels = [active_qg_label, btc_qg_label, bnb_qg_label, alts_qg_label, usd_qg_label];

function contruct_pair(data) {
    let percent = data['priceChangePercent'].slice(0, -2);
    let color = 'red';
    if (parseFloat(percent) > 0) {
        percent = '+' + percent;
        color = 'green';
    }
    return '<div class="row pair" onclick="select_pair(\'' + data['base'] + '\',\'' + data['quote'] + '\')">\n' +
        '<div class="currency">' + data['base'] + '/' + data['quote'] + '</div>\n' +
        '<div class="change ' + color + '">' + percent + '%</div>\n' +
        '<div class="cur_price">' + data['lastPrice'].slice(0, 10) + '</div>\n' +
        '</div>';
}

function refresh_pairs() {
    let pairs = $('#pairs');
    pairs.html('');

    if (current_quote_group === QuoteGroup.BTC) {
        tickers['BTC'].filter(t => parseFloat(t['volume']) > 0).forEach(t => pairs.append(contruct_pair(t)));
    }
    if (current_quote_group === QuoteGroup.BNB) {
        tickers['BNB'].filter(t => parseFloat(t['volume']) > 0).forEach(t => pairs.append(contruct_pair(t)));
    }
    if (current_quote_group === QuoteGroup.ALTS) {
        tickers['ETH'].filter(t => parseFloat(t['volume']) > 0).forEach(t => pairs.append(contruct_pair(t)));
        tickers['XRP'].filter(t => parseFloat(t['volume']) > 0).forEach(t => pairs.append(contruct_pair(t)));
    }
    if (current_quote_group === QuoteGroup.USD) {
        tickers['USDT'].filter(t => parseFloat(t['volume']) > 0).forEach(t => pairs.append(contruct_pair(t)));
        tickers['TUSD'].filter(t => parseFloat(t['volume']) > 0).forEach(t => pairs.append(contruct_pair(t)));
        tickers['PAX'].filter(t => parseFloat(t['volume']) > 0).forEach(t => pairs.append(contruct_pair(t)));
        tickers['USDS'].filter(t => parseFloat(t['volume']) > 0).forEach(t => pairs.append(contruct_pair(t)));
        tickers['USDC'].filter(t => parseFloat(t['volume']) > 0).forEach(t => pairs.append(contruct_pair(t)));
    }
    if (current_quote_group === QuoteGroup.Active) {
        console.log(active_pairs);
        active_pairs.forEach(function(pair){
            tickers[pair.quote].filter(t => t['base'] === pair.base).forEach(t => pairs.append(contruct_pair(t)));
        });
    }
}

function change_quote_group(quote_group) {
    qg_labels[current_quote_group].removeClass('active');
    current_quote_group = quote_group;
    qg_labels[current_quote_group].addClass('active');
    refresh_pairs();
}

let sort_by_price_order = -1;
let sort_by_name_order = -1;
let sort_by_change_order = 1;

function pairs_sort_by_price() {
    sort_by_price_order *= -1;
    $.each(tickers, function (quote, cur_tickers) {
        cur_tickers.sort(
            (a, b) =>
                sort_by_price_order *
                (parseFloat(a['lastPrice']) < parseFloat(b['lastPrice']) ? -1 : 1)
        );
    });
    refresh_pairs();
}

function pairs_sort_by_name() {
    sort_by_name_order *= -1;
    $.each(tickers, function (quote, cur_tickers) {
        cur_tickers.sort(
            (a, b) =>
                sort_by_name_order *
                (a['symbol'] < b['symbol'] ? -1 : 1)
        );
    });
    refresh_pairs();
}

function pairs_sort_by_change() {
    sort_by_change_order *= -1;
    $.each(tickers, function (quote, cur_tickers) {
        cur_tickers.sort(
            (a, b) =>
                sort_by_change_order *
                (parseFloat(a['priceChangePercent']) < parseFloat(b['priceChangePercent']) ? -1 : 1)
        );
    });
    refresh_pairs();
}

change_quote_group(current_quote_group);

function update_assets() {
    $.get('/balance_' + BASE, function(data) {
       base_asset = data;
       $('.asset.base').html(base_asset.free);
    });
    $.get('/balance_' + QUOTE, function(data) {
       quote_asset = data;
       $('.asset.quote').html(quote_asset.free);
    });
}

function select_pair(base, quote, push=true) {
    BASE = base;
    QUOTE = quote;

    // PRECISION
    price_after_comma = precision[BASE + QUOTE]['price_precision'];
    base_after_comma = precision[BASE + QUOTE]['quantity_precision'];
    $( ".input-currency.base" ).html(base);
    $( ".input-currency.quote" ).html(quote);
    $( "input.price" ).attr( "step", precision[BASE + QUOTE]['price_step'] );
    $( "input.amount.base" ).attr( "step", precision[BASE + QUOTE]['quantity_step'] );
    if (quote === 'BTC')
        quote_after_comma = 6;
    else
        quote_after_comma = 2;
    $( "input.amount.quote" ).attr( "step", '1e-' + quote_after_comma );

    $('#pair-label').html('<b>' + BASE + '</b>/' + QUOTE);
    update_chart_data();
    update_assets();
    update_depth_data(function() {
        $('.buy-section input.price').val(trim_price(bids[0][0]));
        $('.sell-section input.price').val(trim_price(asks[0][0]));
    });
    if (push)
        history.pushState({base:BASE, quote: QUOTE}, BASE + '_' + QUOTE, home + BASE + '_' + QUOTE);
}

window.addEventListener('popstate', function (e) {
    select_pair(e.state.base, e.state.quote, false);
});

select_pair(BASE, QUOTE);