var App = App || {};

App.tip = function (message, time) {
    time = time || 4000;
    let body = $('body');
    let obj = body.find('.toast');
    if (!obj.length) {
        obj = $('<div/>', {'class': 'toast'});
        body.append(obj);
    }
    obj.html(message);
    window.setTimeout(function () {
        obj.remove();
    }, time);
};

$(function () {
    $(document).on('click', '.ajax', function () {
        let $this = $(this);
        $this.addClass('loading');
        $.getJSON($this.data('href'), function (result) {
            // $this.removeClass('loading');
            window.location.reload();
        });
    });

    $(document).on('click', '.ajax-modal', function () {
        let $this = $(this);
        let url = $this.data('href');
        $.get(url, function (html) {
            let $container = $("body").find('.modal-container')
            if (!$container.length) {
                $('body').append(html)
            } else {
                $container.html($(html).find('.modal-container').html())
            }
            let $modal = $('.modal');
            $modal.addClass('active');
            $container = $modal.find('.modal-container')
            $container.find('.btn-clear').on('click', function () {
                $modal.removeClass('active');
                $container.html('')
            });
        });
        return false;
    });

});