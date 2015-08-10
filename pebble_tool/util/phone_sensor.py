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
    <body style="font-size: 6vh">
        <h1 style="margin-bottom: 0;">Emulator Control</h1>
        <div class="state" style="margin-top: 0; color: #FF0000">(Connecting)</div>
        <div>
            <div class="stuff" style="display: none;">
                <div>
                    <span class="heading">Heading: ...</span>&deg; (<span class="pebble-heading">...</span>)
                </div>
                <div>
                    <div>X: <span class="accel-x">0</span>N (<span class="pebble-accel-x">0</span>)</div>
                    <div>Y: <span class="accel-y">0</span>N (<span class="pebble-accel-y">0</span>)</div>
                    <div>Z: <span class="accel-z">0</span>N (<span class="pebble-accel-z">0</span>)</div>
                </div>
            </div>
        </div>
    </body>
</html>
"""
