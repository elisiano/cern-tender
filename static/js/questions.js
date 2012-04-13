$(document).ready(function() {

	// Question Create tweaks
	var mydom = $("#id_qfl_size").parent()

	mydom.css("display","none");

	$('#id_question_type').change(function() {
		if($('#id_question_type').val() == 'QuestionFromList') {
			mydom.show('fast');
		}
		else {
			mydom.hide('fast');
		}
	})
    // if the user reloads the page and QuestionFromList is selected,
    // the size field is not displayed, si we explicitly trigger the change event
    	$('#id_question_type').change();

	// Quetion List tweaks
	$('#questions_accordion').accordion({ header:'h3' });
})
