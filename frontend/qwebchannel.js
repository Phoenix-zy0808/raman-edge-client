// SPDX-FileCopyrightText: 2016 The Qt Company Ltd and others.
// SPDX-License-Identifier: LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

//! @file
//! @brief QWebChannel JavaScript Client Implementation

(function() {
    "use strict";

    var QWebChannelMessageEvent = function(type, data) {
        this.initMessageEvent(type, false, false, data, "", "", null);
    };
    QWebChannelMessageEvent.prototype = Object.create(Event.prototype);
    QWebChannelMessageEvent.prototype.constructor = QWebChannelMessageEvent;
    QWebChannelMessageEvent.prototype.initMessageEvent = function(type, bubbles, cancelable, data, origin, lastEventId, source) {
        Event.prototype.initEvent.call(this, type, bubbles, cancelable);
        this.data = data;
        this.origin = origin;
        this.lastEventId = lastEventId;
        this.source = source;
    };

    var QWebChannel = function(transport, callback) {
        var self = this;

        if (!transport) {
            throw new Error("The QWebChannel transport object is null: " + transport);
        }

        this.transport = transport;
        this.objects = {};
        this.signalCache = {};

        transport.onmessage = function(message) {
            self.handleMessage(message);
        };

        transport.send = transport.send || function(data) {
            // Fallback for transports that don't have a send method
            if (transport.postMessage) {
                transport.postMessage(data);
            } else {
                console.error("Transport has neither send nor postMessage");
            }
        };

        this.send = function(data) {
            self.transport.send(JSON.stringify(data));
        };

        this.send({id: 1, type: "init"});

        if (callback) {
            callback(self);
        }
    };

    QWebChannel.prototype.handleMessage = function(message) {
        if (!message.data) {
            return;
        }

        var obj = JSON.parse(message.data);

        if (obj.type === "result") {
            if (obj.id in this.signalCache) {
                var callback = this.signalCache[obj.id];
                delete this.signalCache[obj.id];
                callback(obj.data);
            }
        } else if (obj.type === "signal") {
            var signal = this.signal(obj.signal);
            if (signal) {
                signal.emit.apply(signal, obj.args);
            }
        } else if (obj.type === "object") {
            this.createObject(obj.data);
        } else if (obj.type === "idle") {
            // Handle idle message if needed
        } else {
            console.log("Unhandled message: " + message.data);
        }
    };

    QWebChannel.prototype.createObject = function(data) {
        var self = this;
        var obj = {};
        obj.__id = data.id;
        this.objects[data.id] = obj;

        if (data.methods) {
            for (var i = 0; i < data.methods.length; ++i) {
                var method = data.methods[i];
                obj[method.name] = (function(name, methodInfo) {
                    return function() {
                        var args = Array.prototype.slice.call(arguments);
                        var callback = null;
                        if (args.length > 0 && typeof args[args.length - 1] === "function") {
                            callback = args.pop();
                        }

                        var id = Math.floor(Math.random() * 1000000);
                        if (callback) {
                            self.signalCache[id] = callback;
                        }

                        self.send({
                            id: id,
                            type: "call",
                            object: obj.__id,
                            method: name,
                            args: args
                        });
                    };
                })(method.name, method);
            }
        }

        if (data.signals) {
            for (var i = 0; i < data.signals.length; ++i) {
                var signal = data.signals[i];
                (function(name) {
                    if (!obj[name]) {
                        obj[name] = new QWebChannelSignal(obj.__id, name, self);
                    }
                })(signal.name);
            }
        }

        if (data.properties) {
            for (var i = 0; i < data.properties.length; ++i) {
                var property = data.properties[i];
                obj[property.name] = property.value;
            }
        }

        if (typeof window !== 'undefined' && window.qt && window.qt.webChannelTransport) {
            window.qt.webChannelTransport.objectCreated(obj);
        }
    };

    QWebChannel.prototype.signal = function(signalId) {
        var parts = signalId.split(".");
        var obj = this.objects[parts[0]];
        if (!obj) {
            console.log("Unknown object: " + parts[0]);
            return null;
        }
        var signalName = parts[1];
        if (!obj[signalName]) {
            console.log("Unknown signal: " + signalName);
            return null;
        }
        return obj[signalName];
    };

    var QWebChannelSignal = function(objectId, signalName, channel) {
        this.objectId = objectId;
        this.signalName = signalName;
        this.channel = channel;
        this.callbacks = [];
    };

    QWebChannelSignal.prototype.connect = function(callback) {
        if (typeof callback !== "function") {
            console.error("Invalid callback function");
            return;
        }
        this.callbacks.push(callback);
    };

    QWebChannelSignal.prototype.disconnect = function(callback) {
        var index = this.callbacks.indexOf(callback);
        if (index > -1) {
            this.callbacks.splice(index, 1);
        }
    };

    QWebChannelSignal.prototype.emit = function() {
        for (var i = 0; i < this.callbacks.length; ++i) {
            this.callbacks[i].apply(this, arguments);
        }
    };

    // Export for Node.js
    if (typeof module !== "undefined" && module.exports) {
        module.exports = QWebChannel;
    }

    // Export for browser
    if (typeof window !== "undefined") {
        window.QWebChannel = QWebChannel;
    }
})();
