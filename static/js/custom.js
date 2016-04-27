
/* start search upon pressing [Enter] */
$(document).ready(function() {
    $('#search-form').submit( function() {
        //window.location = '/search/' + $('input[name="toggle"]:checked').val();          
        window.location = '/search/' + $('#search-field').val();
        return false;
    });
});


/* enable line numbers for pre tags
   http://www.jquery2dotnet.com/2013/09/pre-tag-with-line-numbers-using-css3.html */
$(document).ready(function() {
    $("pre").html(function (index, html) {
        return html.trim().replace(/^(.*)$/mg, "<span class=\"line\">$1</span>")
    });
});
