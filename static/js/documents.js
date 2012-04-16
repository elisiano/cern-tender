$(document).ready(function() {

    // this is to give style to the buttons
    $(".document.actions > a").button();

    // handles the systems of a document sorting
    $('#systems > ul').sortable({
        // We define the hook so each time the list
        // is reordered the hidden fields get updated
        // to reflect the new ordering
        beforeStop: function(event, ui) {
                list = $(this).find('li > span.name');
                for(i=0; i< list.length; i++) {
                    //console.log(i + " " +list[i].innerHTML);
                    $('input[name=system_'+ i +']').val(list[i].innerHTML)
                }
        }
    });
    //$('#systems > ul').disableSelection();


});
