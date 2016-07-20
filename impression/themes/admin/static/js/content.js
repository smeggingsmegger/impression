$(function () {
    var elt = $('#tags-div > input');

    elt.tagsinput({
        confirmKeys: [13, 9, 188]
    });
    elt.tagsinput('input').typeahead({
        prefetch: '/get_tags'
    }).bind('typeahead:selected', $.proxy(function (obj, datum) {
        this.tagsinput('add', datum.value);
        this.tagsinput('input').typeahead('setQuery', '');
    }, elt));

    $('.tt-query').blur(function(e) {
        input = $(e.target);
        input.val('');
    });
    var editor = ace.edit("body");
    editor.getSession().setUseWrapMode(true);
    editor.setShowPrintMargin(false);
    editor.setTheme("ace/theme/monokai");
    editor.setOption("spellcheck", true)
    var parser = $("#content-parser option:selected").val();

    if (parser === "mediawiki") {
        editor.getSession().setMode("ace/mode/text");
    }
    else {
        editor.getSession().setMode("ace/mode/" + parser);
    }

    $("#help").click(function(e) {
        e.preventDefault();
        var parser = $("content-parser").val();
        var url = "http://daringfireball.net/projects/markdown/syntax";
        if (parser === "textile") {
            url = "http://redcloth.org/hobix.com/textile/quick.html";
        }
        else if (parser === "mediawiki") {
            url = "http://www.mediawiki.org/wiki/Help:Formatting";
        }
        else if (parser === "html") {
            url = "http://www.webmonkey.com/2010/02/html_cheatsheet/";
        }
        save_content(true, url);
    });
    function show_preview(url) {
        $("#preview-iframe").height($("#page-wrapper").height() - $("#navigation-bar").height());
        $("#preview-iframe").width($("#edit-window").width());
        $("#preview-iframe").attr("src", url);
        $("#preview-div").show();
        $("#edit-window").hide();
        window.scrollTo(0, 0);
    }
    $("#content-parser").change(function() {
        var optionSelected = $("option:selected", this);
        var valueSelected = this.value;
        if (valueSelected !== "mediawiki") {
            editor.getSession().setMode("ace/mode/" + valueSelected);
        }
        else {
            editor.getSession().setMode("ace/mode/text");
        }
    });
    function save_content(showPreview, url) {
        body = editor.getValue();
        title = $('#title').val();
        content_parser = $('#content-parser').val();
        theme = $('#theme').val();
        published_on = $('#published-on').val();
        tags = $('#tags').val();
        page_layout = $('#page-layout').val();
        published = $('#published').is(':checked');
        menu_item = $('#menu-item').is(':checked');
        content_type = impression_URL.segments[1].substring(0, 4);
        user_id = $('#user-id').val();
        var submit = {
            'body': body,
            'title': title,
            'user_id': user_id,
            'parser': content_parser,
            'tags': tags,
            'theme': theme,
            'published': published,
            'menu_item': menu_item,
            'published_on': published_on,
            'page_layout': page_layout,
            'type': content_type
        };

        var editing = false;

        if (impression_URL.segments[2] === "edit") {
            submit.id = impression_URL.segments[3];
            editing = true;
        }

        $.post("/content_create",
            submit
        ).done(function( data ) {
            if (data.success === true && editing === false) {
                window.location.href = "/admin/" + impression_URL.segments[1] + "/edit/" + data.id;
            }
            $.bootbar.show(data.messages[0], { autoDismiss: true });
            if (showPreview) {
                if (!url) {
                    url = "/" + content_type + "/" + data.id;
                }
                show_preview(url);
            }
        });
    }
    $("#close-preview").click(function(e) {
        e.preventDefault();
        $("#preview-div").hide();
        $("#edit-window").show();
        $("#preview-iframe").height(0);
        $("#preview-iframe").width(0);
    });
    $("#preview").click(function(e) {
        e.preventDefault();
        save_content(true);
    });
    $("#save").click(function(e) {
        e.preventDefault();
        save_content();
    });
    $(window).keydown(function (e){
        if ((e.metaKey || e.ctrlKey) && e.keyCode == 83) { /*ctrl+s or command+s*/
            save_content();
            e.preventDefault();
            return false;
        }
    });
});
