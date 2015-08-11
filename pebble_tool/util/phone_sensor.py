SENSOR_PAGE_HTML = """
<html>
    <head>
        <title>Pebble Emulator Control</title>
        <link rel="stylesheet" type="text/css" href="static/stylesheets/sensors.css">
        <script src="static/js/textdecoder.js" type="text/javascript"></script>
        <script src="static/js/jquery-2.1.4.min.js" type="text/javascript"></script>
        <script src="static/js/underscore-min.js" type="text/javascript"></script>
        <script src="static/js/backbone-min.js" type="text/javascript"></script>
        <script type="text/javascript">var host = {websocket_host}; var port = {websocket_port};</script>
        <script src="static/js/websocket.js" type="text/javascript"></script>
        <script src="static/js/sensors.js" type="text/javascript"></script>
    </head>
    <body>
        <h1 style="margin-bottom: 0;">Emulator Control</h1>
        <div class="state" style="margin-top: 0; color: #FF0000">(Connecting)</div>
        <div>
            <div class="stuff" style="display: none;">
                <input type="checkbox" class="use_sensors" name="use_sensors" value="1" checked> Use built-in sensors
                <div>
                    <span class="heading">Heading: ...</span>&deg; (<span class="pebble-heading">...</span>)
                </div>
                <div>
                    <div><span class="accel-x">0</span>m/s2 (<span class="pebble-accel-x">0</span>)</div>
                    -x <input class="accel-x-slider" type="range" min="-4000" max="4000" step="1" value="0" /> +x
                    <div><span class="accel-y">0</span>m/s2 (<span class="pebble-accel-y">0</span>)</div>
                    -y <input class="accel-y-slider" type="range" min="-4000" max="4000" step="1" value="0" /> +y
                    <div><span class="accel-z">0</span>m/s2 (<span class="pebble-accel-z">0</span>)</div>
                    -z <input class="accel-z-slider" type="range" min="-4000" max="4000" step="1" value="0" /> +z
                </div>
            </div>
        </div>
    </body>
</html>
"""
