
/* start search upon pressing [Enter] */
$(document).ready(function() {
    $('#search-form').submit( function() {
        //window.location = '/search/' + $('input[name="toggle"]:checked').val();          
        window.location = '/search/' + $('#search-field').val();
        return false;
    });
});

