$(document).ready(function() {

    // this is to give style to the buttons
    $(".document.actions > a").button();

    // handles the systems of a document sorting
    $('#systems > ul.sortable').sortable({
        // We define the hook so each time the list
        // is reordered the hidden fields get updated
        // to reflect the new ordering
        beforeStop: function(event, ui) {
                list = $(this).find('li > span.name');
                for(i=0; i<list.length; i++) {
                    $('input[name=system_'+ i +']').val(list[i].innerHTML)
                }
        }
    });
    //$('#systems > ul').disableSelection();

    // Sortable list of the Sections
    $('#sections > ul.sortable').sortable({
        beforeStop: function(event,ui) {
                list = $(this).find('li > span.name');
                for(i=0; i<list.length; i++) {
                    $('input[name=section_'+ i +']').val(list[i].innerHTML)
                }
        }
    })
    // Sortable list of the questions in the section
    $('#questions > ul.sortable').sortable({
        beforeStop: function(event,ui) {
                list = $(this).find('li > span.name');
                for(i=0; i<list.length; i++) {
                    $('input[name=question_'+ i +']').val(list[i].innerHTML)
                }
        }
    })
    // Sortable list of the contacts in the document
    $('#contacts > ul.sortable').sortable({
        beforeStop: function(event,ui) {
                list = $(this).find('li > span.name');
                for(i=0; i<list.length; i++) {
                    $('input[name=contact_'+ i +']').val(list[i].innerHTML)
                }
        }
    })


});
