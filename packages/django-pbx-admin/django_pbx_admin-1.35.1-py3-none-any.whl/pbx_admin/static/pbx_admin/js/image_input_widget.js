$(document).ready(function() {
    $(document).on('error', '.image-input-widget', function() {
        var $img = $(this);
        var fallbackUrl = $img.data('fallback-url');
        var fallbackGif = $img.data('fallback-gif');
        
        if (fallbackUrl) {
            $img.off('error');
            $img.attr('src', fallbackUrl);
        }
        if (!fallbackUrl && fallbackGif) {
            $img.off('error');
            $img.attr('src', fallbackGif);
        }
    });
});
