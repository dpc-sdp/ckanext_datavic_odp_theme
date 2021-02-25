function checkboxClick(event, parent) {
    var target = event.target ? event.target : event.srcElement
    var label = (parent) ? target.querySelector('label') : target.parentElement
    if (label.getAttribute('class').match(/chk-label-active/i)) {
        label.setAttribute('class', '')
        if (label.firstElementChild) label.firstElementChild.setAttribute('class', 'jcf-class-jcf-hidden chk-area chk chk-unchecked')
        else label.firstChild.setAttribute('class', 'jcf-class-jcf-hidden chk-area chk chk-unchecked')
        if (document.querySelector("#orderEmail")) document.querySelector("#orderEmail").setAttribute("class", "")
    }
    else {
        label.setAttribute('class', 'chk-label-active')
        if (label.firstElementChild) label.firstElementChild.setAttribute('class', 'jcf-class-jcf-hidden chk-area chk chk-checked')
        else label.firstChild.setAttribute('class', 'jcf-class-jcf-hidden chk-area chk chk-checked')
        var target = event.target ? event.target : event.srcElement
        if (target.parentElement.querySelector('.resource-download')) target.parentElement.querySelector('.resource-download').click()
        target.parentElement.parentElement.parentElement.querySelector('.resource-download').click()
    }
    target.className = target.className+' custom-check';
}

function checkTerms(event) {
    var target = event.target ? event.target : event.srcElement
    if (!target.parentElement.querySelector('.chk-label-active')) {
        return false
    }
    else if (target.innerHTML.match(/order/i)) {
        showOrderEmail(target.getAttribute('href'))
        return false
    }
}

function showOrderEmail(href){
    document.querySelector('#orderEmail').setAttribute('class', 'shown')
    document.querySelector('#orderEmail').setAttribute('data-href', href)
}

function checkOrder(e){
    var email = document.querySelector('#order-email').value
    console.log(email);
    var dog = email.indexOf('@')
    var dot = email.lastIndexOf('.')
    if (dog < 1 || dot < dog || dot - dog < 2 || email.length - 2 < dot) {
        var inputs = document.querySelectorAll('#orderEmail input'), i;

        for (i = 0; i < inputs.length; ++i) {
          inputs[i].setAttribute('class', 'error');
        }
    }
    else {
        window.location = document.querySelector('#orderEmail').getAttribute('data-href').replace(':emailAddress', encodeURI(email))
    }

}

function checkboxKey(event) {
    if (event.keyCode === 32) {
        checkboxClick(event, true)
        event.preventDefault();
        return false;
    } else if (event.keyCode === 13) {
        var target = event.target ? event.target : event.srcElement
        target.querySelector('.resource-download').click()
    }
}
