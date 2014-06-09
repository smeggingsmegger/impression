$(function () {
    $("#profile-form").submit(function(e) {
        e.preventDefault();
        var submit = {};
        $(".profile").each(function(index, elm) {
            element = $(elm);
            submit[element.attr('name')] = element.val();
        });
        $.post("/admin/users/edit/post",
            submit
        ).done(function( data ) {
            $.bootbar.show(data.messages[0], { autoDismiss: true });
        });
    });
});

