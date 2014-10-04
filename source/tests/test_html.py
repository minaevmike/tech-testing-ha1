def site_with_google_analitcs():
    return """"<!DOCTYPE html><html>
<head>

</head>
<body

<script>
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/ga.js','ga');
ga('create', 'UA-52744155-1', 'auto');
ga('send', 'pageview');
</script>
</body>
</script></html>"""


def blank_site():
    return """<html><head></head><body></body></html>"""


def bad_content_length_in_meta_tag():
    return """
    <html><head>
     <meta http-equiv="refresh" content="aaa?;bad_length;aaa?">
    </head><body></body></html>
    """


def no_http_equiv_in_meta_tag():
    return """
    <html><head>
     <meta content="aaa?;url=google.com">
    </head><body></body></html>
    """

def bad_content_url_in_meta_tag():
    return """
    <html><head>
     <meta http-equiv="refresh" content="aaa?;urlgoogle.com">
    </head><body></body></html>
    """


def good_meta_tag():
    return """
    <html><head>
     <meta http-equiv="refresh" content="aaa?;url=google.com">
    </head><body></body></html>
    """