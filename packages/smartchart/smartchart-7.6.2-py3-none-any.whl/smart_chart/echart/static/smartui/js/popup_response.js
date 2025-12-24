/*global opener */
(function() {
    'use strict';
    let initData = JSON.parse(document.getElementById('django-admin-popup-response-constants').dataset.popupResponse);
    try{
    switch(initData.action) {
    case 'change':
        opener.dismissChangeRelatedObjectPopup(window, initData.value, initData.obj, initData.new_value);
        break;
    case 'delete':
        opener.dismissDeleteRelatedObjectPopup(window, initData.value);
        break;
    default:
        opener.dismissAddRelatedObjectPopup(window, initData.value, initData.obj);
        break;
    }
    }catch{
        if(self!==top){if(parent.myapp){parent.myapp.dialogVisible=false;}else{parent.location.reload()}}else{window.close();}
        }
})();
