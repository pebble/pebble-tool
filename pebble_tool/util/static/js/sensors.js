var Compass = {
    Uncalibrated: 0,
    Calibrating: 1,
    Calibrated: 2
};

var pebble = new PebbleWebSocket(host, port);
pebble.on('open', function() {
    var samples = [];
    var use_sensors;

    var updateAccelText = _.throttle(function(accel) {
        var pebble_accel = convert_to_pebble_accel(accel);
        $('.accel-x').text(accel.x.toFixed(2));
        $('.accel-y').text(accel.y.toFixed(2));
        $('.accel-z').text(accel.z.toFixed(2));
        $('.pebble-accel-x').text(pebble_accel[0]);
        $('.pebble-accel-y').text(pebble_accel[1]);
        $('.pebble-accel-z').text(pebble_accel[2]);
        $('.accel-x-slider').val(pebble_accel[0]);
        $('.accel-y-slider').val(pebble_accel[1]);
        $('.accel-z-slider').val(pebble_accel[2]);
    }, 100);
    var updateHeadingText = function(heading) {
        $('.heading').text(Math.round(heading));
        $('.pebble-heading').text(convert_to_pebble_heading(heading));
    };
    var updateCompassOrientation = function(heading) {
        $('.compass-bg').rotate(Math.round(heading));
        $('.needle').rotate(0);
    };


    var convert_to_pebble_accel = function(accel) {
        return _.map(accel, function(v, k) { return (v / 0.00981).toFixed(0)|0});
    };
    var convert_to_pebble_heading = function(heading) {
        return (Math.ceil(heading * 65536 / 360)).toFixed(0)|0;
    };

    var send_queued_samples = _.throttle(function() {
        if(pebble != null) {
            pebble.emu_set_accel(samples);
        }
        samples = [];
    }, 300);


    var isReversed = /Android/i.test(navigator.userAgent);
    window.ondevicemotion = _.throttle(function(e) {
        if(!$('.use_sensors').prop('checked')) { return; }
        var accel = _.clone(e.accelerationIncludingGravity);
        if(accel.x == null) { return; }
        if(isReversed) {
            accel.x = -accel.x;
            accel.y = -accel.y;
            accel.z = -accel.z;
        }
        samples.push(convert_to_pebble_accel(accel));
        updateAccelText(accel);
        send_queued_samples();
    }, 10);
    window.ondeviceorientation = _.throttle(function(e) {
        if(!$('.use_sensors').prop('checked')) { return; }
        if(e.webkitCompassHeading !== undefined) {
            var heading = e.webkitCompassHeading;
        } else if(e.alpha !== null) {
            var heading = window.innerWidth < window.innerHeight ? e.alpha : e.alpha + 90;
        } else {
            return;
        }
        updateHeadingText(heading);
        updateCompassOrientation(heading);
        if(pebble != null) {
            pebble.emu_set_compass(convert_to_pebble_heading(heading), Compass.Calibrated);
        }
    }, 500);

    $('input[type=range]').on("input", function() {
        $('.use_sensors').prop('checked', false);
        var accel = {
            x: parseInt($('.accel-x-slider').val(), 10)*0.00981,
            y: parseInt($('.accel-y-slider').val(), 10)*0.00981,
            z: parseInt($('.accel-z-slider').val(), 10)*0.00981
        };
        samples.push(convert_to_pebble_accel(accel));
        updateAccelText(accel);
        send_queued_samples();
    });

    if(window.DeviceMotionEvent && window.DeviceOrientationEvent) {
        $('.state').text("Transmitting");
        $('.stuff').show();
    } else {
        $('.state').text("Not Supported");
    }
});

pebble.on('close', function() {
    window.ondevicemotion = null;
    window.ondeviceorientation = null;
    $('.state').text("Disconnected");
    $('.stuff').hide();
    pebble = null;
});
