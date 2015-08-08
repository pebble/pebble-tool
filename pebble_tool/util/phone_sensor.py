SENSOR_PAGE_HTML = """
<html>
    <head>
        <title>Pebble Emulator Control</title>
        <script src="static/js/textdecoder.js" type="text/javascript"></script>
        <script src="static/js/jquery-2.1.4.min.js" type="text/javascript"></script>
        <script src="static/js/underscore-min.js" type="text/javascript"></script>
        <script src="static/js/backbone-min.js" type="text/javascript"></script>
        <script type="text/javascript">var host = {websocket_host}; var port = {websocket_port};</script>
        <script src="static/js/websocket.js" type="text/javascript"></script>
        <script src="static/js/sensors.js" type="text/javascript"></script>
    </head>
    <body style="font-size: 10vh">
        <h1 style="font-size: 100%; margin-bottom: 0;">Emulator Control</h1>
        <div class="state" style="margin-top: 0; font-size: 60%; color: #FF0000">(Connecting)</div>
        <div>
            <div class="stuff" style="display: none; margin-top: 40px; font-size: 72%;">
                <h3>Heading:
                    <span class="heading" style="font-weight: lighter;">...</span>&deg;
                </h3>
                <h3>Acceleration:
                    <span class="accel-x" style="font-weight: lighter;">0</span>,
                    <span class="accel-y" style="font-weight: lighter;">0</span>,
                    <span class="accel-z" style="font-weight: lighter;">0</span>
                </h3>
            </div>
        </div>
    </body>
</html>
"""
