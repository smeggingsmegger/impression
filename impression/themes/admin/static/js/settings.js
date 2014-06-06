$(function () {
    $("#settings-form").submit(function(e) {
        e.preventDefault();
        var submit = {};
        $(".setting").each(function(index, elm) {
            element = $(elm);
            submit[element.attr('name')] = element.val();
        });
        $.post("/admin/settings/post",
            submit
        ).done(function( data ) {
            $.bootbar.show(data.messages[0], { autoDismiss: true });
        });
    });
});

