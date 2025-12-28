"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["5633"],{56750:function(t,e,a){a.d(e,{a:function(){return o}});a(74423);var r=a(31136),i=a(41144);function o(t,e){var a=(0,i.m)(t.entity_id),o=void 0!==e?e:null==t?void 0:t.state;if(["button","event","input_button","scene"].includes(a))return o!==r.Hh;if((0,r.g0)(o))return!1;if(o===r.KF&&"alert"!==a)return!1;switch(a){case"alarm_control_panel":return"disarmed"!==o;case"alert":return"idle"!==o;case"cover":case"valve":return"closed"!==o;case"device_tracker":case"person":return"not_home"!==o;case"lawn_mower":return["mowing","error"].includes(o);case"lock":return"locked"!==o;case"media_player":return"standby"!==o;case"vacuum":return!["idle","docked","paused"].includes(o);case"plant":return"problem"===o;case"group":return["on","home","open","locked","problem"].includes(o);case"timer":return"active"===o;case"camera":return"streaming"===o}return!0}},70358:function(t,e,a){a.d(e,{Se:function(){return u},mT:function(){return v}});a(23792),a(44114),a(26099),a(31415),a(17642),a(58004),a(33853),a(45876),a(32475),a(15024),a(31698),a(62953);var r=a(31136),i=a(94741),o=(a(62062),a(18111),a(61701),a(41144));a(31432),a(72712),a(94490),a(18237),a(42762);var n=a(93777),s=(a(2892),a(56750)),c=new Set(["alarm_control_panel","alert","automation","binary_sensor","calendar","camera","climate","cover","device_tracker","fan","group","humidifier","input_boolean","lawn_mower","light","lock","media_player","person","plant","remote","schedule","script","siren","sun","switch","timer","update","vacuum","valve","water_heater","weather"]),u=(t,e)=>{if((void 0!==e?e:null==t?void 0:t.state)===r.Hh)return"var(--state-unavailable-color)";var a,i=h(t,e);return i?(a=i,Array.isArray(a)?a.reverse().reduce(((t,e)=>`var(${e}${t?`, ${t}`:""})`),void 0):`var(${a})`):void 0},l=(t,e,a)=>{var r=void 0!==a?a:e.state,i=(0,s.a)(e,a);return d(t,e.attributes.device_class,r,i)},d=(t,e,a,r)=>{var i=[],o=(0,n.Y)(a,"_"),s=r?"active":"inactive";return e&&i.push(`--state-${t}-${e}-${o}-color`),i.push(`--state-${t}-${o}-color`,`--state-${t}-${s}-color`,`--state-${s}-color`),i},h=(t,e)=>{var a=void 0!==e?e:null==t?void 0:t.state,r=(0,o.m)(t.entity_id),n=t.attributes.device_class;if("sensor"===r&&"battery"===n){var s=(t=>{var e=Number(t);if(!isNaN(e))return e>=70?"--state-sensor-battery-high-color":e>=30?"--state-sensor-battery-medium-color":"--state-sensor-battery-low-color"})(a);if(s)return[s]}if("group"===r){var u=(t=>{var e=t.attributes.entity_id||[],a=(0,i.A)(new Set(e.map((t=>(0,o.m)(t)))));return 1===a.length?a[0]:void 0})(t);if(u&&c.has(u))return l(u,t,e)}if(c.has(r))return l(r,t,e)},v=t=>t.attributes.brightness&&"plant"!==(0,o.m)(t.entity_id)?`brightness(${(t.attributes.brightness+245)/5}%)`:""},93777:function(t,e,a){a.d(e,{Y:function(){return r}});a(26099),a(84864),a(57465),a(27495),a(38781),a(25440);var r=function(t){var e,a=arguments.length>1&&void 0!==arguments[1]?arguments[1]:"_",r="àáâäæãåāăąабçćčđďдèéêëēėęěеёэфğǵгḧхîïíīįìıİийкłлḿмñńǹňнôöòóœøōõőоṕпŕřрßśšşșсťțтûüùúūǘůűųувẃẍÿýыžźżз·",i=`aaaaaaaaaaabcccdddeeeeeeeeeeefggghhiiiiiiiiijkllmmnnnnnoooooooooopprrrsssssstttuuuuuuuuuuvwxyyyzzzz${a}`,o=new RegExp(r.split("").join("|"),"g"),n={"ж":"zh","х":"kh","ц":"ts","ч":"ch","ш":"sh","щ":"shch","ю":"iu","я":"ia"};return""===t?e="":""===(e=t.toString().toLowerCase().replace(o,(t=>i.charAt(r.indexOf(t)))).replace(/[а-я]/g,(t=>n[t]||"")).replace(/(\d),(?=\d)/g,"$1").replace(/[^a-z0-9]+/g,a).replace(new RegExp(`(${a})\\1+`,"g"),"$1").replace(new RegExp(`^${a}+`),"").replace(new RegExp(`${a}+$`),""))&&(e="unknown"),e}},41079:function(t,e,a){a.d(e,{E:function(){return i}});var r,i=(0,a(96196).AH)(r||(r=(t=>t)`
  ha-state-icon[data-domain="alarm_control_panel"][data-state="pending"],
  ha-state-icon[data-domain="alarm_control_panel"][data-state="arming"],
  ha-state-icon[data-domain="alarm_control_panel"][data-state="triggered"],
  ha-state-icon[data-domain="lock"][data-state="jammed"] {
    animation: pulse 1s infinite;
  }

  @keyframes pulse {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0;
    }
    100% {
      opacity: 1;
    }
  }

  /* Color the icon if unavailable */
  ha-state-icon[data-state="unavailable"] {
    color: var(--state-unavailable-color);
  }
`))},91720:function(t,e,a){a.a(t,(async function(t,e){try{var r=a(44734),i=a(56038),o=a(69683),n=a(6454),s=a(25460),c=(a(28706),a(23792),a(62062),a(18111),a(7588),a(36033),a(26099),a(23500),a(62953),a(62826)),u=a(96196),l=a(77845),d=a(32288),h=a(29485),v=a(41144),b=a(97382),f=a(70358),p=a(41079),m=a(73275),y=a(62424),_=a(4148),g=t([_]);_=(g.then?(await g)():g)[0];var k,$,w,j=t=>t,O=function(t){function e(){var t;(0,r.A)(this,e);for(var a=arguments.length,i=new Array(a),n=0;n<a;n++)i[n]=arguments[n];return(t=(0,o.A)(this,e,[].concat(i))).icon=!0,t._iconStyle={},t}return(0,n.A)(e,t),(0,i.A)(e,[{key:"connectedCallback",value:function(){var t,a;(0,s.A)(e,"connectedCallback",this,3)([]),this.hasUpdated&&void 0===this.overrideImage&&(null!==(t=this.stateObj)&&void 0!==t&&t.attributes.entity_picture||null!==(a=this.stateObj)&&void 0!==a&&a.attributes.entity_picture_local)&&this.requestUpdate("stateObj")}},{key:"disconnectedCallback",value:function(){var t,a;(0,s.A)(e,"disconnectedCallback",this,3)([]),void 0===this.overrideImage&&(null!==(t=this.stateObj)&&void 0!==t&&t.attributes.entity_picture||null!==(a=this.stateObj)&&void 0!==a&&a.attributes.entity_picture_local)&&(this.style.backgroundImage="")}},{key:"_stateColor",get:function(){var t,e=this.stateObj?(0,b.t)(this.stateObj):void 0;return null!==(t=this.stateColor)&&void 0!==t?t:"light"===e}},{key:"render",value:function(){var t=this.stateObj;if(!t&&!this.overrideIcon&&!this.overrideImage)return(0,u.qy)(k||(k=j`<div class="missing">
        <ha-svg-icon .path=${0}></ha-svg-icon>
      </div>`),"M13 14H11V9H13M13 18H11V16H13M1 21H23L12 2L1 21Z");var e=this.getClass();if(e&&e.forEach(((t,e)=>{t?this.classList.add(e):this.classList.remove(e)})),!this.icon)return u.s6;var a=t?(0,b.t)(t):void 0;return(0,u.qy)($||($=j`<ha-state-icon
      .hass=${0}
      style=${0}
      data-domain=${0}
      data-state=${0}
      .icon=${0}
      .stateObj=${0}
    ></ha-state-icon>`),this.hass,(0,h.W)(this._iconStyle),(0,d.J)(a),(0,d.J)(null==t?void 0:t.state),this.overrideIcon,t)}},{key:"willUpdate",value:function(t){if((0,s.A)(e,"willUpdate",this,3)([t]),t.has("stateObj")||t.has("overrideImage")||t.has("overrideIcon")||t.has("stateColor")||t.has("color")){var a=this.stateObj,r={},i="";if(this.icon=!0,a){var o=(0,v.m)(a.entity_id);if(void 0===this.overrideImage)if(!a.attributes.entity_picture_local&&!a.attributes.entity_picture||this.overrideIcon){if(this.color)r.color=this.color;else if(this._stateColor){var n=(0,f.Se)(a);if(n&&(r.color=n),a.attributes.rgb_color&&(r.color=`rgb(${a.attributes.rgb_color.join(",")})`),a.attributes.brightness){var c=a.attributes.brightness;if("number"!=typeof c){var u=`Type error: state-badge expected number, but type of ${a.entity_id}.attributes.brightness is ${typeof c} (${c})`;console.warn(u)}r.filter=(0,f.mT)(a)}if(a.attributes.hvac_action){var l=a.attributes.hvac_action;l in y.sx?r.color=(0,f.Se)(a,y.sx[l]):delete r.color}}}else{var d=a.attributes.entity_picture_local||a.attributes.entity_picture;this.hass&&(d=this.hass.hassUrl(d)),"camera"===o&&(d=(0,m.su)(d,80,80)),i=`url(${d})`,this.icon=!1}else if(this.overrideImage){var h=this.overrideImage;this.hass&&(h=this.hass.hassUrl(h)),i=`url(${h})`,this.icon=!1}}this._iconStyle=r,this.style.backgroundImage=i}}},{key:"getClass",value:function(){var t=new Map(["has-no-radius","has-media-image","has-image"].map((t=>[t,!1])));if(this.stateObj){var e=(0,v.m)(this.stateObj.entity_id);"update"===e?t.set("has-no-radius",!0):"media_player"===e||"camera"===e?t.set("has-media-image",!0):""!==this.style.backgroundImage&&t.set("has-image",!0)}return t}}],[{key:"styles",get:function(){return[p.E,(0,u.AH)(w||(w=j`
        :host {
          position: relative;
          display: inline-flex;
          width: 40px;
          color: var(--state-icon-color);
          border-radius: var(--state-badge-border-radius, 50%);
          height: 40px;
          background-size: cover;
          box-sizing: border-box;
          --state-inactive-color: initial;
          align-items: center;
          justify-content: center;
        }
        :host(.has-image) {
          border-radius: var(--state-badge-with-image-border-radius, 50%);
        }
        :host(.has-media-image) {
          border-radius: var(--state-badge-with-media-image-border-radius, 8%);
        }
        :host(.has-no-radius) {
          border-radius: var(--ha-border-radius-square);
        }
        :host(:focus) {
          outline: none;
        }
        :host(:not([icon]):focus) {
          border: 2px solid var(--divider-color);
        }
        :host([icon]:focus) {
          background: var(--divider-color);
        }
        ha-state-icon {
          transition:
            color 0.3s ease-in-out,
            filter 0.3s ease-in-out;
        }
        .missing {
          color: #fce588;
        }
      `))]}}])}(u.WF);(0,c.__decorate)([(0,l.MZ)({attribute:!1})],O.prototype,"stateObj",void 0),(0,c.__decorate)([(0,l.MZ)({attribute:!1})],O.prototype,"overrideIcon",void 0),(0,c.__decorate)([(0,l.MZ)({attribute:!1})],O.prototype,"overrideImage",void 0),(0,c.__decorate)([(0,l.MZ)({attribute:!1})],O.prototype,"stateColor",void 0),(0,c.__decorate)([(0,l.MZ)()],O.prototype,"color",void 0),(0,c.__decorate)([(0,l.MZ)({type:Boolean,reflect:!0})],O.prototype,"icon",void 0),(0,c.__decorate)([(0,l.wk)()],O.prototype,"_iconStyle",void 0),customElements.define("state-badge",O),e()}catch(A){e(A)}}))},4148:function(t,e,a){a.a(t,(async function(t,e){try{var r=a(44734),i=a(56038),o=a(69683),n=a(6454),s=a(62826),c=a(96196),u=a(77845),l=a(45847),d=a(97382),h=a(43197),v=(a(22598),a(60961),t([h]));h=(v.then?(await v)():v)[0];var b,f,p,m,y=t=>t,_=function(t){function e(){return(0,r.A)(this,e),(0,o.A)(this,e,arguments)}return(0,n.A)(e,t),(0,i.A)(e,[{key:"render",value:function(){var t,e,a=this.icon||this.stateObj&&(null===(t=this.hass)||void 0===t||null===(t=t.entities[this.stateObj.entity_id])||void 0===t?void 0:t.icon)||(null===(e=this.stateObj)||void 0===e?void 0:e.attributes.icon);if(a)return(0,c.qy)(b||(b=y`<ha-icon .icon=${0}></ha-icon>`),a);if(!this.stateObj)return c.s6;if(!this.hass)return this._renderFallback();var r=(0,h.fq)(this.hass,this.stateObj,this.stateValue).then((t=>t?(0,c.qy)(f||(f=y`<ha-icon .icon=${0}></ha-icon>`),t):this._renderFallback()));return(0,c.qy)(p||(p=y`${0}`),(0,l.T)(r))}},{key:"_renderFallback",value:function(){var t=(0,d.t)(this.stateObj);return(0,c.qy)(m||(m=y`
      <ha-svg-icon
        .path=${0}
      ></ha-svg-icon>
    `),h.l[t]||h.lW)}}])}(c.WF);(0,s.__decorate)([(0,u.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:!1})],_.prototype,"stateObj",void 0),(0,s.__decorate)([(0,u.MZ)({attribute:!1})],_.prototype,"stateValue",void 0),(0,s.__decorate)([(0,u.MZ)()],_.prototype,"icon",void 0),_=(0,s.__decorate)([(0,u.EM)("ha-state-icon")],_),e()}catch(g){e(g)}}))},73275:function(t,e,a){a.d(e,{su:function(){return o},wv:function(){return n}});var r=a(61397),i=a(50264),o=(a(28706),a(54193),(t,e,a)=>`${t}&width=${e}&height=${a}`),n=function(){var t=(0,i.A)((0,r.A)().m((function t(e,a,i){var o,n;return(0,r.A)().w((function(t){for(;;)switch(t.n){case 0:return o={type:"camera/stream",entity_id:a},i&&(o.format=i),t.n=1,e.callWS(o);case 1:return(n=t.v).url=e.hassUrl(n.url),t.a(2,n)}}),t)})));return function(e,a,r){return t.apply(this,arguments)}}()},62424:function(t,e,a){a.d(e,{sx:function(){return i},v5:function(){return r}});a(72712),a(26099);var r="none",i=(["auto","heat_cool","heat","cool","dry","fan_only","off"].reduce(((t,e,a)=>(t[e]=a,t)),{}),{cooling:"cool",defrosting:"heat",drying:"dry",fan:"fan_only",heating:"heat",idle:"off",off:"off",preheating:"heat"})}}]);
//# sourceMappingURL=5633.2745c9adc93136f8.js.map