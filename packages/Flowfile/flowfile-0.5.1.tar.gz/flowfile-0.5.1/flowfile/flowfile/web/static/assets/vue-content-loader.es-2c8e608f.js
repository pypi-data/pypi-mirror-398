import { d as defineComponent, f as createVNode, l as computed } from "./index-5429bbf8.js";
var uid = function() {
  return Math.random().toString(36).substring(2);
};
var ContentLoader = defineComponent({
  name: "ContentLoader",
  props: {
    width: {
      type: [Number, String]
    },
    height: {
      type: [Number, String]
    },
    viewBox: {
      type: String
    },
    preserveAspectRatio: {
      type: String,
      "default": "xMidYMid meet"
    },
    speed: {
      type: Number,
      "default": 2
    },
    baseUrl: {
      type: String,
      "default": ""
    },
    primaryColor: {
      type: String,
      "default": "#f9f9f9"
    },
    secondaryColor: {
      type: String,
      "default": "#ecebeb"
    },
    primaryOpacity: {
      type: Number,
      "default": 1
    },
    secondaryOpacity: {
      type: Number,
      "default": 1
    },
    uniqueKey: {
      type: String
    },
    animate: {
      type: Boolean,
      "default": true
    }
  },
  setup: function setup(props) {
    var idClip = computed(function() {
      return props.uniqueKey ? "".concat(props.uniqueKey, "-idClip") : uid();
    });
    var idGradient = computed(function() {
      return props.uniqueKey ? "".concat(props.uniqueKey, "-idGradient") : uid();
    });
    var width = computed(function() {
      var _a;
      return (_a = props.width) !== null && _a !== void 0 ? _a : 400;
    });
    var height = computed(function() {
      var _a;
      return (_a = props.height) !== null && _a !== void 0 ? _a : 130;
    });
    var computedViewBox = computed(function() {
      var _a;
      return (_a = props.viewBox) !== null && _a !== void 0 ? _a : "0 0 ".concat(width.value, " ").concat(height.value);
    });
    return {
      idClip,
      idGradient,
      computedViewBox
    };
  },
  render: function render() {
    return createVNode("svg", {
      "width": this.width,
      "height": this.height,
      "viewBox": this.computedViewBox,
      "version": "1.1",
      "preserveAspectRatio": this.preserveAspectRatio
    }, [createVNode("rect", {
      "style": {
        fill: "url(".concat(this.baseUrl, "#").concat(this.idGradient, ")")
      },
      "clip-path": "url(".concat(this.baseUrl, "#").concat(this.idClip, ")"),
      "x": "0",
      "y": "0",
      "width": "100%",
      "height": "100%"
    }, null), createVNode("defs", null, [createVNode("clipPath", {
      "id": this.idClip
    }, [this.$slots["default"] ? this.$slots["default"]() : createVNode("rect", {
      "x": "0",
      "y": "0",
      "rx": "5",
      "ry": "5",
      "width": "100%",
      "height": "100%"
    }, null)]), createVNode("linearGradient", {
      "id": this.idGradient
    }, [createVNode("stop", {
      "offset": "0%",
      "stop-color": this.primaryColor,
      "stop-opacity": this.primaryOpacity
    }, [this.animate ? createVNode("animate", {
      "attributeName": "offset",
      "values": "-2; 1",
      "dur": "".concat(this.speed, "s"),
      "repeatCount": "indefinite"
    }, null) : null]), createVNode("stop", {
      "offset": "50%",
      "stop-color": this.secondaryColor,
      "stop-opacity": this.secondaryOpacity
    }, [this.animate ? createVNode("animate", {
      "attributeName": "offset",
      "values": "-1.5; 1.5",
      "dur": "".concat(this.speed, "s"),
      "repeatCount": "indefinite"
    }, null) : null]), createVNode("stop", {
      "offset": "100%",
      "stop-color": this.primaryColor,
      "stop-opacity": this.primaryOpacity
    }, [this.animate ? createVNode("animate", {
      "attributeName": "offset",
      "values": "-1; 2",
      "dur": "".concat(this.speed, "s"),
      "repeatCount": "indefinite"
    }, null) : null])])])]);
  }
});
var CodeLoader = defineComponent(function(props, _a) {
  var attrs = _a.attrs;
  return function() {
    return createVNode(ContentLoader, attrs, {
      "default": function _default() {
        return [createVNode("rect", {
          "x": "0",
          "y": "0",
          "rx": "3",
          "ry": "3",
          "width": "70",
          "height": "10"
        }, null), createVNode("rect", {
          "x": "80",
          "y": "0",
          "rx": "3",
          "ry": "3",
          "width": "100",
          "height": "10"
        }, null), createVNode("rect", {
          "x": "190",
          "y": "0",
          "rx": "3",
          "ry": "3",
          "width": "10",
          "height": "10"
        }, null), createVNode("rect", {
          "x": "15",
          "y": "20",
          "rx": "3",
          "ry": "3",
          "width": "130",
          "height": "10"
        }, null), createVNode("rect", {
          "x": "155",
          "y": "20",
          "rx": "3",
          "ry": "3",
          "width": "130",
          "height": "10"
        }, null), createVNode("rect", {
          "x": "15",
          "y": "40",
          "rx": "3",
          "ry": "3",
          "width": "90",
          "height": "10"
        }, null), createVNode("rect", {
          "x": "115",
          "y": "40",
          "rx": "3",
          "ry": "3",
          "width": "60",
          "height": "10"
        }, null), createVNode("rect", {
          "x": "185",
          "y": "40",
          "rx": "3",
          "ry": "3",
          "width": "60",
          "height": "10"
        }, null), createVNode("rect", {
          "x": "0",
          "y": "60",
          "rx": "3",
          "ry": "3",
          "width": "30",
          "height": "10"
        }, null)];
      }
    });
  };
});
export {
  CodeLoader as C
};
