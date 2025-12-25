$(document).ready(function() {
	$(".toggle > *").hide();
	$(".toggle .header").show();
	$(".toggle .header").click(function() {
		$(this).parent().children().not(".header").slideToggle(400);
		$(this).parent().children(".header").toggleClass("open");
	});
});