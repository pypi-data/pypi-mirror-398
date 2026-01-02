//Copy pasted from https://stackoverflow.com/a/18652401/8767538, I'm a noob webdev lol
function setCookie(key, value, expiry) {
	var expires = new Date();
	expires.setTime(expires.getTime() + (expiry * 24 * 60 * 60 * 1000));
	document.cookie = key + '=' + value + ';path=/;expires=' + expires.toUTCString();
}
function getCookie(key) {
	var keyValue = document.cookie.match('(^|;) ?' + key + '=([^;]*)(;|$)');
	return keyValue ? keyValue[2] : null;
}
function eraseCookie(key) {
	var keyValue = getCookie(key);
	setCookie(key, keyValue, '-1');
}

var inputTypeTranslator = {
	"b": "input", //Checkbox
	"r": "input", //Radio
	"i": "input", //Input
	"d": "select", //Dropdown
	"t": "textarea" //Text area
};

function autocomplete(action, actionIds, previousKeys){
	//We DON'T need to check if a field "group" is "open", the input object will always be there
	for(var i = 0; i < actionIds.length; i++){
		var id = actionIds[i].replaceAll(/[^a-zA-Z0-9\-\_\+\/\$]+/gm, "");
		if(!previousKeys.includes(id)){

			var value = action[id];
			var type = value.charAt(0); //first char identifies the type
			value = value.substring(1);

			htmlType = inputTypeTranslator[type];
			if(htmlType === undefined) { console.log("Unknown type: " + type); continue; }

			var sp = id.split("$"); //Use "$" as a SINGLE wildcard in ids
			var elements = null;
			if(sp.length > 1) {
				elements = $(htmlType + '[id^=' + sp[0] + '][id$=' + sp[1] + ']'); //Apply the same addons/questions to every cart position. There's no known way to differentiate between those
			} else elements = $(htmlType + '[id=' + id + ']');

			var foundDisabledElement = false;
			for(var j = 0; j < elements.length; j++){
				obj = elements[j];
				if(obj.disabled) {
					foundDisabledElement = true;
					continue;
				}

				switch(type){
					case 'r': {
						obj.checked = false;
						obj.click();
						setTimeout(function(o){ o.dispatchEvent(new Event('change')); }, 100, obj);
						break;
					}
					case 'd':
					case 't':
					case 'i': {
						obj.value = value;
						obj.dispatchEvent(new Event('change'));
						obj.focus(); //Just to be sure
						break;
					}
					case 'b': {
						var flag = value === '1';
						if(obj.checked !== flag) obj.click();
						break;
					}
					default: {
						console.log("Unknown type: " + type);
						break;
					}
				}
			}
			
			if(elements.length > 0 && !foundDisabledElement) previousKeys.push(id);
		}
	}

	setCookie("pretix_autocart_previous", previousKeys.join("@"), 1);
	setTimeout(function(){ autocomplete(action, actionIds, previousKeys); }, 1500);
}

function decodeBase64(base64) {
	// https://stackoverflow.com/a/64752311
	// Decoding b64 with utf8 symbols like ž (hi Pur3bolt! :D) was giving us wrong results. This properly decodes it
	const text = atob(base64);
	const length = text.length;
	const bytes = new Uint8Array(length);
	for (let i = 0; i < length; i++) {
		bytes[i] = text.charCodeAt(i);
	}
	const decoder = new TextDecoder(); // default is utf-8
	return decoder.decode(bytes);
}

$(document).ready(function(){
	$.get("/autocart/pubkey", function(data, status){

		var urlParams = new URLSearchParams("?" + (window.location.hash.substring(1)));
		var action = urlParams.get('a');
		var signature = urlParams.get('s');
		var isDataInUrl = true;

		if(action === null && signature === null){
			isDataInUrl = false;
			action = getCookie("pretix_autocart_action");
			signature = getCookie("pretix_autocart_signature");
			if(action === null && signature === null) return;
		}

		var jse = new JSEncrypt();
		jse.setPublicKey(data);
		var result = jse.verify(action, signature.replaceAll("-", "+").replaceAll("_", "/"), CryptoJS.SHA256);
		if(!result){ console.log("Invalid signature detected!"); return; }

		action = action.replaceAll(/[^a-zA-Z0-9\-\_\+\/]+/gm, ""); //Better sanitize to not destroy cookies :P
		signature = signature.replaceAll(/[^a-zA-Z0-9\-\_\+\/]+/gm, "");
		if(isDataInUrl){
			setCookie("pretix_autocart_action", action, 1);
			setCookie("pretix_autocart_signature", signature, 1);
			eraseCookie("pretix_autocart_previous");
		}

		var previousKeys = getCookie("pretix_autocart_previous"); //Get previously filled questions/cart positions. We give the chance to the user to edit their cart
		previousKeys = (previousKeys === null || previousKeys === "" || isDataInUrl) ? [] : previousKeys.split("@"); //Dumb way of splitting

		action = JSON.parse(decodeBase64(action.replaceAll("-", "+").replaceAll("_", "/")));
		actionIds = Object.keys(action);

		autocomplete(action, actionIds, previousKeys);
	});
});