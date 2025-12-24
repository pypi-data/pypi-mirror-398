window.getLanuage = function (key) {
    if (!window.Lanuages) {
        return "";
    }
    let val = Lanuages[key];
    if (!val || val == "") {
        val = key;
    }
    return val
}