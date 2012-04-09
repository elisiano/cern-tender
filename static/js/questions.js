$(document).ready(function() {
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
})
