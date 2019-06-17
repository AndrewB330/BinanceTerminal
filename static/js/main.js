let price_after_comma = 2;
let base_after_comma = 6;
let quote_after_comma = 2;

function trim_zeros(str, after_comma) {
    if (str.indexOf('.') === -1) return str + '.' + '0'.repeat(after_comma);
    if (after_comma === 0)
        return str.slice(0, str.indexOf('.'));
    return str.slice(0, str.indexOf('.') + after_comma + 1);
}

function trim_price(str) {
    return trim_zeros(str, price_after_comma);
}

function trim_base_amount(str) {
    return trim_zeros(str, base_after_comma);
}

function trim_quote_amount(str) {
    return trim_zeros(str, quote_after_comma);
}

function timeConverter(timestamp){
  let a = new Date(timestamp);
  let months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  let year = a.getFullYear();
  let month = months[a.getMonth()];
  let date = ('0' + a.getDate()).substr(-2);
  let hour = ('0' + a.getHours()).substr(-2);
  let min = ('0' + a.getMinutes()).substr(-2);
  let sec = ('0' + a.getSeconds()).substr(-2);
  return date + ' ' + month + ' ' + year + ' ' + hour + ':' + min + ':' + sec;
}