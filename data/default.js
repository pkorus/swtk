function synchButtonStates(element) {
	/* Apply proper coloring of toggle buttons */
	element.find(".toggleButton").each(function() {
		cssClasses = $(this).attr('data-css');
		if (cssClasses.length == 0) return
		var cssClassList = $.trim(cssClasses).split(" ");
		if ($('.'+cssClassList.join(', .')).length > 0) {
			$(this).addClass('activeButton').removeClass('inactiveButton');
		} else {
			$(this).addClass('inactiveButton').removeClass('activeButton');
		}
	});	
}

$(document).ready(function() {

	synchButtonStates($('body'));

	$(".toggleButton").click(function() {

		/* Get css classes' names for (de)activation */
		cssClasses = $(this).attr('data-css');
		if (cssClasses.length == 0) return
		var cssClassList = $.trim(cssClasses).split(" ");

		/* Look for visible items */
		var shownItem = 0;
		for(i = 0; i < cssClassList.length; i++) { shownItem += $('.'+cssClassList[i]).length; }

		/* Toggle highlighting of given items */
		for(i = 0; i < cssClassList.length; i++){
			if (shownItem > 0) {
				$('.'+cssClassList[i]).removeClass(cssClassList[i]).addClass('_'+cssClassList[i]);
			} else {
				$('._'+cssClassList[i]).removeClass('_'+cssClassList[i]).addClass(cssClassList[i]);
			}
		}

		/* Update current and any "children" buttons  */
		synchButtonStates($(this).parents('.reportItem'));
	});

	$(".reportItem #detailsButton").click(function() {
	  $(this).parent().parent().find('.reportDetails').toggle('blind');
	});

	$(".reportItem #helpButton").click(function() {
	  $(this).parent().parent().find('.reportHelp').toggle('blind');
	});

	$("#expand-button").click(function() {
		if ($('.reportDetails:hidden').length > 0) {
			$('.reportDetails').show('blind');
		} else {
			$('.reportDetails').hide('blind');
		}
	});

	$("#clear-highlights").click(function() {
		if ($('.reportTitle .toggleButton.activeButton').length > 0) {
			$('.reportTitle .toggleButton.activeButton').click();
		} else {
			$('.reportTitle .toggleButton.inactiveButton').click();
		}
	});

	$("#verb-report").click(function() {
		$('.toggleButton[data-css~=buriedVerb].inactiveButton').click();
		$('.toggleButton[data-css~=passiveVerb].inactiveButton').click();
		$('.toggleButton[data-css=weakVerb].inactiveButton').click();
		$('.toggleButton[data-css=pos_verb].inactiveButton').click();		
	});

	$("#frequent-phrases").click(function() {
		$('.reportTitle .toggleButton[data-css~=rareWord_1].inactiveButton').click();
		$('.reportTitle .toggleButton[data-css~=bigram_1].inactiveButton').click();
		$('.reportTitle .toggleButton[data-css~=trigram_1].inactiveButton').click();
		$('.reportTitle .toggleButton[data-css~=abbrev_1].inactiveButton').click();
	});

	$("#clutter").click(function() {
		$('.reportTitle .toggleButton[data-css~=filterWord].inactiveButton').click();
		$('.toggleButton[data-css=pos_adverb].inactiveButton').click();
	});

	$("#general-guidelines").click(function() {
		$('.reportItem#getting-started #helpButton').click();
	});

});