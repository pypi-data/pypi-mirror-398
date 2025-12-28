"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["3538"],{38852:function(e,t,i){i.d(t,{b:function(){return r}});var a=i(31432),r=(i(23792),i(36033),i(26099),i(84864),i(57465),i(27495),i(69479),i(38781),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(62953),(e,t)=>{if(e===t)return!0;if(e&&t&&"object"==typeof e&&"object"==typeof t){if(e.constructor!==t.constructor)return!1;var i,o;if(Array.isArray(e)){if((o=e.length)!==t.length)return!1;for(i=o;0!=i--;)if(!r(e[i],t[i]))return!1;return!0}if(e instanceof Map&&t instanceof Map){if(e.size!==t.size)return!1;var n,s=(0,a.A)(e.entries());try{for(s.s();!(n=s.n()).done;)if(i=n.value,!t.has(i[0]))return!1}catch(p){s.e(p)}finally{s.f()}var l,d=(0,a.A)(e.entries());try{for(d.s();!(l=d.n()).done;)if(i=l.value,!r(i[1],t.get(i[0])))return!1}catch(p){d.e(p)}finally{d.f()}return!0}if(e instanceof Set&&t instanceof Set){if(e.size!==t.size)return!1;var c,u=(0,a.A)(e.entries());try{for(u.s();!(c=u.n()).done;)if(i=c.value,!t.has(i[0]))return!1}catch(p){u.e(p)}finally{u.f()}return!0}if(ArrayBuffer.isView(e)&&ArrayBuffer.isView(t)){if((o=e.length)!==t.length)return!1;for(i=o;0!=i--;)if(e[i]!==t[i])return!1;return!0}if(e.constructor===RegExp)return e.source===t.source&&e.flags===t.flags;if(e.valueOf!==Object.prototype.valueOf)return e.valueOf()===t.valueOf();if(e.toString!==Object.prototype.toString)return e.toString()===t.toString();var h=Object.keys(e);if((o=h.length)!==Object.keys(t).length)return!1;for(i=o;0!=i--;)if(!Object.prototype.hasOwnProperty.call(t,h[i]))return!1;for(i=o;0!=i--;){var g=h[i];if(!r(e[g],t[g]))return!1}return!0}return e!=e&&t!=t})},25854:function(e,t,i){var a=i(44734),r=i(56038),o=i(69683),n=i(6454),s=i(62826),l=i(77845),d=i(74687),c=function(e){function t(){return(0,a.A)(this,t),(0,o.A)(this,t,[d.nx,d.o9,e=>({device_id:e||"",trigger:"device",domain:"",entity_id:""})])}return(0,n.A)(t,e),(0,r.A)(t,[{key:"NO_AUTOMATION_TEXT",get:function(){return this.hass.localize("ui.panel.config.devices.automation.triggers.no_triggers")}},{key:"UNKNOWN_AUTOMATION_TEXT",get:function(){return this.hass.localize("ui.panel.config.devices.automation.triggers.unknown_trigger")}}])}(i(7078).V);c=(0,s.__decorate)([(0,l.EM)("ha-device-trigger-picker")],c)},47916:function(e,t,i){i.d(t,{x:function(){return a}});var a="__ANY_STATE_IGNORE_ATTRIBUTES__"},90832:function(e,t,i){var a,r,o=i(61397),n=i(50264),s=i(44734),l=i(56038),d=i(69683),c=i(6454),u=i(25460),h=(i(28706),i(62826)),g=i(36387),p=i(34875),v=i(7731),_=i(96196),f=i(77845),m=i(94333),y=i(92542),b=(i(70524),e=>e),A=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,d.A)(this,t,[].concat(a))).checkboxDisabled=!1,e.indeterminate=!1,e}return(0,c.A)(t,e),(0,l.A)(t,[{key:"onChange",value:(i=(0,n.A)((0,o.A)().m((function e(i){return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:(0,u.A)(t,"onChange",this,3)([i]),(0,y.r)(this,i.type);case 1:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"render",value:function(){var e={"mdc-deprecated-list-item__graphic":this.left,"mdc-deprecated-list-item__meta":!this.left},t=this.renderText(),i=this.graphic&&"control"!==this.graphic&&!this.left?this.renderGraphic():_.s6,r=this.hasMeta&&this.left?this.renderMeta():_.s6,o=this.renderRipple();return(0,_.qy)(a||(a=b` ${0} ${0} ${0}
      <span class=${0}>
        <ha-checkbox
          reducedTouchTarget
          tabindex=${0}
          .checked=${0}
          .indeterminate=${0}
          ?disabled=${0}
          @change=${0}
        >
        </ha-checkbox>
      </span>
      ${0} ${0}`),o,i,this.left?"":t,(0,m.H)(e),this.tabindex,this.selected,this.indeterminate,this.disabled||this.checkboxDisabled,this.onChange,this.left?t:"",r)}}]);var i}(g.h);A.styles=[v.R,p.R,(0,_.AH)(r||(r=b`
      :host {
        --mdc-theme-secondary: var(--primary-color);
      }

      :host([graphic="avatar"]) .mdc-deprecated-list-item__graphic,
      :host([graphic="medium"]) .mdc-deprecated-list-item__graphic,
      :host([graphic="large"]) .mdc-deprecated-list-item__graphic,
      :host([graphic="control"]) .mdc-deprecated-list-item__graphic {
        margin-inline-end: var(--mdc-list-item-graphic-margin, 16px);
        margin-inline-start: 0px;
        direction: var(--direction);
      }
      .mdc-deprecated-list-item__meta {
        flex-shrink: 0;
        direction: var(--direction);
        margin-inline-start: auto;
        margin-inline-end: 0;
      }
      .mdc-deprecated-list-item__graphic {
        margin-top: var(--check-list-item-graphic-margin-top);
      }
      :host([graphic="icon"]) .mdc-deprecated-list-item__graphic {
        margin-inline-start: 0;
        margin-inline-end: var(--mdc-list-item-graphic-margin, 32px);
      }
    `))],(0,h.__decorate)([(0,f.MZ)({type:Boolean,attribute:"checkbox-disabled"})],A.prototype,"checkboxDisabled",void 0),(0,h.__decorate)([(0,f.MZ)({type:Boolean})],A.prototype,"indeterminate",void 0),A=(0,h.__decorate)([(0,f.EM)("ha-check-list-item")],A)},23442:function(e,t,i){i.d(t,{$:function(){return a}});i(52675),i(89463),i(16280),i(34782),i(18111),i(7588),i(26099),i(23500);var a=e=>{var t={};return e.forEach((e=>{var i,r;if(void 0!==(null===(i=e.description)||void 0===i?void 0:i.suggested_value)&&null!==(null===(r=e.description)||void 0===r?void 0:r.suggested_value))t[e.name]=e.description.suggested_value;else if("default"in e)t[e.name]=e.default;else if("expandable"===e.type){var o=a(e.schema);(e.required||Object.keys(o).length)&&(t[e.name]=o)}else if(e.required){if("boolean"===e.type)t[e.name]=!1;else if("string"===e.type)t[e.name]="";else if("integer"===e.type)t[e.name]="valueMin"in e?e.valueMin:0;else if("constant"===e.type)t[e.name]=e.value;else if("float"===e.type)t[e.name]=0;else if("select"===e.type){if(e.options.length){var n=e.options[0];t[e.name]=Array.isArray(n)?n[0]:n}}else if("positive_time_period_dict"===e.type)t[e.name]={hours:0,minutes:0,seconds:0};else if("selector"in e){var s,l=e.selector;if("device"in l)t[e.name]=null!==(s=l.device)&&void 0!==s&&s.multiple?[]:"";else if("entity"in l){var d;t[e.name]=null!==(d=l.entity)&&void 0!==d&&d.multiple?[]:""}else if("area"in l){var c;t[e.name]=null!==(c=l.area)&&void 0!==c&&c.multiple?[]:""}else if("label"in l){var u;t[e.name]=null!==(u=l.label)&&void 0!==u&&u.multiple?[]:""}else if("boolean"in l)t[e.name]=!1;else if("addon"in l||"attribute"in l||"file"in l||"icon"in l||"template"in l||"text"in l||"theme"in l||"object"in l)t[e.name]="";else if("number"in l){var h,g;t[e.name]=null!==(h=null===(g=l.number)||void 0===g?void 0:g.min)&&void 0!==h?h:0}else if("select"in l){var p;if(null!==(p=l.select)&&void 0!==p&&p.options.length){var v=l.select.options[0],_="string"==typeof v?v:v.value;t[e.name]=l.select.multiple?[_]:_}}else if("country"in l){var f;null!==(f=l.country)&&void 0!==f&&null!==(f=f.countries)&&void 0!==f&&f.length&&(t[e.name]=l.country.countries[0])}else if("language"in l){var m;null!==(m=l.language)&&void 0!==m&&null!==(m=m.languages)&&void 0!==m&&m.length&&(t[e.name]=l.language.languages[0])}else if("duration"in l)t[e.name]={hours:0,minutes:0,seconds:0};else if("time"in l)t[e.name]="00:00:00";else if("date"in l||"datetime"in l){var y=(new Date).toISOString().slice(0,10);t[e.name]=`${y}T00:00:00`}else if("color_rgb"in l)t[e.name]=[0,0,0];else if("color_temp"in l){var b,A;t[e.name]=null!==(b=null===(A=l.color_temp)||void 0===A?void 0:A.min_mireds)&&void 0!==b?b:153}else if("action"in l||"trigger"in l||"condition"in l)t[e.name]=[];else if("media"in l||"target"in l)t[e.name]={};else{if(!("state"in l))throw new Error(`Selector ${Object.keys(l)[0]} not supported in initial form data`);var $;t[e.name]=null!==($=l.state)&&void 0!==$&&$.multiple?[]:""}}}else;})),t}},58103:function(e,t,i){i.a(e,(async function(e,a){try{i.d(t,{S:function(){return A}});var r=i(44734),o=i(56038),n=i(69683),s=i(6454),l=i(62826),d=i(96196),c=i(77845),u=i(45847),h=i(41144),g=i(43197),p=i(7053),v=(i(22598),i(60961),e([g]));g=(v.then?(await v)():v)[0];var _,f,m,y,b=e=>e,A={calendar:"M19,19H5V8H19M16,1V3H8V1H6V3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3H18V1M17,12H12V17H17V12Z",device:"M3 6H21V4H3C1.9 4 1 4.9 1 6V18C1 19.1 1.9 20 3 20H7V18H3V6M13 12H9V13.78C8.39 14.33 8 15.11 8 16C8 16.89 8.39 17.67 9 18.22V20H13V18.22C13.61 17.67 14 16.88 14 16S13.61 14.33 13 13.78V12M11 17.5C10.17 17.5 9.5 16.83 9.5 16S10.17 14.5 11 14.5 12.5 15.17 12.5 16 11.83 17.5 11 17.5M22 8H16C15.5 8 15 8.5 15 9V19C15 19.5 15.5 20 16 20H22C22.5 20 23 19.5 23 19V9C23 8.5 22.5 8 22 8M21 18H17V10H21V18Z",event:"M10,9A1,1 0 0,1 11,8A1,1 0 0,1 12,9V13.47L13.21,13.6L18.15,15.79C18.68,16.03 19,16.56 19,17.14V21.5C18.97,22.32 18.32,22.97 17.5,23H11C10.62,23 10.26,22.85 10,22.57L5.1,18.37L5.84,17.6C6.03,17.39 6.3,17.28 6.58,17.28H6.8L10,19V9M11,5A4,4 0 0,1 15,9C15,10.5 14.2,11.77 13,12.46V11.24C13.61,10.69 14,9.89 14,9A3,3 0 0,0 11,6A3,3 0 0,0 8,9C8,9.89 8.39,10.69 9,11.24V12.46C7.8,11.77 7,10.5 7,9A4,4 0 0,1 11,5M11,3A6,6 0 0,1 17,9C17,10.7 16.29,12.23 15.16,13.33L14.16,12.88C15.28,11.96 16,10.56 16,9A5,5 0 0,0 11,4A5,5 0 0,0 6,9C6,11.05 7.23,12.81 9,13.58V14.66C6.67,13.83 5,11.61 5,9A6,6 0 0,1 11,3Z",state:"M6.27 17.05C6.72 17.58 7 18.25 7 19C7 20.66 5.66 22 4 22S1 20.66 1 19 2.34 16 4 16C4.18 16 4.36 16 4.53 16.05L7.6 10.69L5.86 9.7L9.95 8.58L11.07 12.67L9.33 11.68L6.27 17.05M20 16C18.7 16 17.6 16.84 17.18 18H11V16L8 19L11 22V20H17.18C17.6 21.16 18.7 22 20 22C21.66 22 23 20.66 23 19S21.66 16 20 16M12 8C12.18 8 12.36 8 12.53 7.95L15.6 13.31L13.86 14.3L17.95 15.42L19.07 11.33L17.33 12.32L14.27 6.95C14.72 6.42 15 5.75 15 5C15 3.34 13.66 2 12 2S9 3.34 9 5 10.34 8 12 8Z",geo_location:"M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z",homeassistant:p.mdiHomeAssistant,mqtt:"M21,9L17,5V8H10V10H17V13M7,11L3,15L7,19V16H14V14H7V11Z",numeric_state:"M4,17V9H2V7H6V17H4M22,15C22,16.11 21.1,17 20,17H16V15H20V13H18V11H20V9H16V7H20A2,2 0 0,1 22,9V10.5A1.5,1.5 0 0,1 20.5,12A1.5,1.5 0 0,1 22,13.5V15M14,15V17H8V13C8,11.89 8.9,11 10,11H12V9H8V7H12A2,2 0 0,1 14,9V11C14,12.11 13.1,13 12,13H10V15H14Z",sun:"M12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,2L14.39,5.42C13.65,5.15 12.84,5 12,5C11.16,5 10.35,5.15 9.61,5.42L12,2M3.34,7L7.5,6.65C6.9,7.16 6.36,7.78 5.94,8.5C5.5,9.24 5.25,10 5.11,10.79L3.34,7M3.36,17L5.12,13.23C5.26,14 5.53,14.78 5.95,15.5C6.37,16.24 6.91,16.86 7.5,17.37L3.36,17M20.65,7L18.88,10.79C18.74,10 18.47,9.23 18.05,8.5C17.63,7.78 17.1,7.15 16.5,6.64L20.65,7M20.64,17L16.5,17.36C17.09,16.85 17.62,16.22 18.04,15.5C18.46,14.77 18.73,14 18.87,13.21L20.64,17M12,22L9.59,18.56C10.33,18.83 11.14,19 12,19C12.82,19 13.63,18.83 14.37,18.56L12,22Z",conversation:"M8,7A2,2 0 0,1 10,9V14A2,2 0 0,1 8,16A2,2 0 0,1 6,14V9A2,2 0 0,1 8,7M14,14C14,16.97 11.84,19.44 9,19.92V22H7V19.92C4.16,19.44 2,16.97 2,14H4A4,4 0 0,0 8,18A4,4 0 0,0 12,14H14M21.41,9.41L17.17,13.66L18.18,10H14A2,2 0 0,1 12,8V4A2,2 0 0,1 14,2H20A2,2 0 0,1 22,4V8C22,8.55 21.78,9.05 21.41,9.41Z",tag:"M18,6H13A2,2 0 0,0 11,8V10.28C10.41,10.62 10,11.26 10,12A2,2 0 0,0 12,14C13.11,14 14,13.1 14,12C14,11.26 13.6,10.62 13,10.28V8H16V16H8V8H10V6H8L6,6V18H18M20,20H4V4H20M20,2H4A2,2 0 0,0 2,4V20A2,2 0 0,0 4,22H20C21.11,22 22,21.1 22,20V4C22,2.89 21.11,2 20,2Z",template:"M8,3A2,2 0 0,0 6,5V9A2,2 0 0,1 4,11H3V13H4A2,2 0 0,1 6,15V19A2,2 0 0,0 8,21H10V19H8V14A2,2 0 0,0 6,12A2,2 0 0,0 8,10V5H10V3M16,3A2,2 0 0,1 18,5V9A2,2 0 0,0 20,11H21V13H20A2,2 0 0,0 18,15V19A2,2 0 0,1 16,21H14V19H16V14A2,2 0 0,1 18,12A2,2 0 0,1 16,10V5H14V3H16Z",time:"M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z",time_pattern:"M11,17A1,1 0 0,0 12,18A1,1 0 0,0 13,17A1,1 0 0,0 12,16A1,1 0 0,0 11,17M11,3V7H13V5.08C16.39,5.57 19,8.47 19,12A7,7 0 0,1 12,19A7,7 0 0,1 5,12C5,10.32 5.59,8.78 6.58,7.58L12,13L13.41,11.59L6.61,4.79V4.81C4.42,6.45 3,9.05 3,12A9,9 0 0,0 12,21A9,9 0 0,0 21,12A9,9 0 0,0 12,3M18,12A1,1 0 0,0 17,11A1,1 0 0,0 16,12A1,1 0 0,0 17,13A1,1 0 0,0 18,12M6,12A1,1 0 0,0 7,13A1,1 0 0,0 8,12A1,1 0 0,0 7,11A1,1 0 0,0 6,12Z",webhook:"M10.46,19C9,21.07 6.15,21.59 4.09,20.15C2.04,18.71 1.56,15.84 3,13.75C3.87,12.5 5.21,11.83 6.58,11.77L6.63,13.2C5.72,13.27 4.84,13.74 4.27,14.56C3.27,16 3.58,17.94 4.95,18.91C6.33,19.87 8.26,19.5 9.26,18.07C9.57,17.62 9.75,17.13 9.82,16.63V15.62L15.4,15.58L15.47,15.47C16,14.55 17.15,14.23 18.05,14.75C18.95,15.27 19.26,16.43 18.73,17.35C18.2,18.26 17.04,18.58 16.14,18.06C15.73,17.83 15.44,17.46 15.31,17.04L11.24,17.06C11.13,17.73 10.87,18.38 10.46,19M17.74,11.86C20.27,12.17 22.07,14.44 21.76,16.93C21.45,19.43 19.15,21.2 16.62,20.89C15.13,20.71 13.9,19.86 13.19,18.68L14.43,17.96C14.92,18.73 15.75,19.28 16.75,19.41C18.5,19.62 20.05,18.43 20.26,16.76C20.47,15.09 19.23,13.56 17.5,13.35C16.96,13.29 16.44,13.36 15.97,13.53L15.12,13.97L12.54,9.2H12.32C11.26,9.16 10.44,8.29 10.47,7.25C10.5,6.21 11.4,5.4 12.45,5.44C13.5,5.5 14.33,6.35 14.3,7.39C14.28,7.83 14.11,8.23 13.84,8.54L15.74,12.05C16.36,11.85 17.04,11.78 17.74,11.86M8.25,9.14C7.25,6.79 8.31,4.1 10.62,3.12C12.94,2.14 15.62,3.25 16.62,5.6C17.21,6.97 17.09,8.47 16.42,9.67L15.18,8.95C15.6,8.14 15.67,7.15 15.27,6.22C14.59,4.62 12.78,3.85 11.23,4.5C9.67,5.16 8.97,7 9.65,8.6C9.93,9.26 10.4,9.77 10.97,10.11L11.36,10.32L8.29,15.31C8.32,15.36 8.36,15.42 8.39,15.5C8.88,16.41 8.54,17.56 7.62,18.05C6.71,18.54 5.56,18.18 5.06,17.24C4.57,16.31 4.91,15.16 5.83,14.67C6.22,14.46 6.65,14.41 7.06,14.5L9.37,10.73C8.9,10.3 8.5,9.76 8.25,9.14Z",persistent_notification:"M13 11H11V5H13M13 15H11V13H13M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z",zone:"M12,2C15.31,2 18,4.66 18,7.95C18,12.41 12,19 12,19C12,19 6,12.41 6,7.95C6,4.66 8.69,2 12,2M12,6A2,2 0 0,0 10,8A2,2 0 0,0 12,10A2,2 0 0,0 14,8A2,2 0 0,0 12,6M20,19C20,21.21 16.42,23 12,23C7.58,23 4,21.21 4,19C4,17.71 5.22,16.56 7.11,15.83L7.75,16.74C6.67,17.19 6,17.81 6,18.5C6,19.88 8.69,21 12,21C15.31,21 18,19.88 18,18.5C18,17.81 17.33,17.19 16.25,16.74L16.89,15.83C18.78,16.56 20,17.71 20,19Z",list:"M7,5H21V7H7V5M7,13V11H21V13H7M4,4.5A1.5,1.5 0 0,1 5.5,6A1.5,1.5 0 0,1 4,7.5A1.5,1.5 0 0,1 2.5,6A1.5,1.5 0 0,1 4,4.5M4,10.5A1.5,1.5 0 0,1 5.5,12A1.5,1.5 0 0,1 4,13.5A1.5,1.5 0 0,1 2.5,12A1.5,1.5 0 0,1 4,10.5M7,19V17H21V19H7M4,16.5A1.5,1.5 0 0,1 5.5,18A1.5,1.5 0 0,1 4,19.5A1.5,1.5 0 0,1 2.5,18A1.5,1.5 0 0,1 4,16.5Z"},$=function(e){function t(){return(0,r.A)(this,t),(0,n.A)(this,t,arguments)}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){if(this.icon)return(0,d.qy)(_||(_=b`<ha-icon .icon=${0}></ha-icon>`),this.icon);if(!this.trigger)return d.s6;if(!this.hass)return this._renderFallback();var e=(0,g.ab)(this.hass,this.trigger).then((e=>e?(0,d.qy)(f||(f=b`<ha-icon .icon=${0}></ha-icon>`),e):this._renderFallback()));return(0,d.qy)(m||(m=b`${0}`),(0,u.T)(e))}},{key:"_renderFallback",value:function(){var e=(0,h.m)(this.trigger);return(0,d.qy)(y||(y=b`
      <ha-svg-icon
        .path=${0}
      ></ha-svg-icon>
    `),A[this.trigger]||g.l[e])}}])}(d.WF);(0,l.__decorate)([(0,c.MZ)({attribute:!1})],$.prototype,"hass",void 0),(0,l.__decorate)([(0,c.MZ)()],$.prototype,"trigger",void 0),(0,l.__decorate)([(0,c.MZ)()],$.prototype,"icon",void 0),$=(0,l.__decorate)([(0,c.EM)("ha-trigger-icon")],$),a()}catch(k){a(k)}}))},44600:function(e,t,i){var a,r,o,n=i(44734),s=i(56038),l=i(69683),d=i(25460),c=i(6454),u=(i(16034),i(62826)),h=i(96196),g=i(77845),p=i(94333),v=i(29485),_=i(97382),f=i(47268),m=e=>e,y=function(e){function t(){return(0,n.A)(this,t),(0,l.A)(this,t,arguments)}return(0,c.A)(t,e),(0,s.A)(t,[{key:"willUpdate",value:function(e){if((0,d.A)(t,"willUpdate",this,3)([e]),e.has("user"))this._getPersonPicture();else{var i=e.get("hass");if(this._personEntityId&&i&&this.hass.states[this._personEntityId]!==i.states[this._personEntityId]){var a=this.hass.states[this._personEntityId];a?this._personPicture=a.attributes.entity_picture:this._getPersonPicture()}else!this._personEntityId&&i&&this._getPersonPicture()}}},{key:"render",value:function(){if(!this.hass||!this.user)return h.s6;var e=this._personPicture;if(e)return(0,h.qy)(a||(a=m`<div
        style=${0}
        class="picture"
      ></div>`),(0,v.W)({backgroundImage:`url(${this.hass.hassUrl(e)})`}));var t=(0,f._2)(this.user.name);return(0,h.qy)(r||(r=m`<div
      class="initials ${0}"
    >
      ${0}
    </div>`),(0,p.H)({long:t.length>2}),t)}},{key:"_getPersonPicture",value:function(){if(this._personEntityId=void 0,this._personPicture=void 0,this.hass&&this.user)for(var e=0,t=Object.values(this.hass.states);e<t.length;e++){var i=t[e];if(i.attributes.user_id===this.user.id&&"person"===(0,_.t)(i)){this._personEntityId=i.entity_id,this._personPicture=i.attributes.entity_picture;break}}}}])}(h.WF);y.styles=(0,h.AH)(o||(o=m`
    :host {
      display: block;
      width: 40px;
      height: 40px;
    }
    .picture {
      width: 100%;
      height: 100%;
      background-size: cover;
      border-radius: var(--ha-border-radius-circle);
    }
    .initials {
      display: inline-flex;
      justify-content: center;
      align-items: center;
      box-sizing: border-box;
      width: 100%;
      height: 100%;
      border-radius: var(--ha-border-radius-circle);
      background-color: var(--light-primary-color);
      text-decoration: none;
      color: var(--text-light-primary-color, var(--primary-text-color));
      overflow: hidden;
    }
    .initials.long {
      font-size: var(--ha-font-size-s);
    }
  `)),(0,u.__decorate)([(0,g.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,u.__decorate)([(0,g.MZ)({attribute:!1})],y.prototype,"user",void 0),(0,u.__decorate)([(0,g.wk)()],y.prototype,"_personPicture",void 0),y=(0,u.__decorate)([(0,g.EM)("ha-user-badge")],y)},53977:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),r=i(50264),o=i(44734),n=i(56038),s=i(69683),l=i(6454),d=i(25460),c=(i(28706),i(2008),i(23792),i(62062),i(18111),i(22489),i(61701),i(36033),i(26099),i(62953),i(62826)),u=i(96196),h=i(77845),g=i(22786),p=i(92542),v=i(47268),_=(i(94343),i(96943)),f=(i(44600),e([_]));_=(f.then?(await f)():f)[0];var m,y,b,A,$,k,C,w,M,x=e=>e,H=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(a))).value="",e.disabled=!1,e.usersMap=(0,g.A)((e=>e?new Map(e.map((e=>[e.id,e]))):new Map)),e._valueRenderer=t=>{var i=e.usersMap(e.users).get(t);return i?(0,u.qy)(y||(y=x`
      <ha-user-badge
        slot="start"
        .hass=${0}
        .user=${0}
      ></ha-user-badge>
      <span slot="headline">${0}</span>
    `),e.hass,i,i.name):(0,u.qy)(m||(m=x` <span slot="headline">${0}</span> `),t)},e._rowRenderer=t=>t.user?(0,u.qy)(C||(C=x`
      <ha-combo-box-item type="button" compact>
        <ha-user-badge
          slot="start"
          .hass=${0}
          .user=${0}
        ></ha-user-badge>
        <span slot="headline">${0}</span>
      </ha-combo-box-item>
    `),e.hass,t.user,t.primary):(0,u.qy)(b||(b=x`<ha-combo-box-item type="button" compact>
        ${0}
        <span slot="headline">${0}</span>
        ${0}
      </ha-combo-box-item>`),t.icon?(0,u.qy)(A||(A=x`<ha-icon slot="start" .icon=${0}></ha-icon>`),t.icon):t.icon_path?(0,u.qy)($||($=x`<ha-svg-icon
                slot="start"
                .path=${0}
              ></ha-svg-icon>`),t.icon_path):u.s6,t.primary,t.secondary?(0,u.qy)(k||(k=x`<span slot="supporting-text">${0}</span>`),t.secondary):u.s6),e._getUsers=(0,g.A)((e=>e?e.filter((e=>!e.system_generated)).map((e=>({id:e.id,primary:e.name,domain_name:e.name,search_labels:[e.name,e.id,e.username].filter(Boolean),sorting_label:e.name,user:e}))):[])),e._getItems=()=>e._getUsers(e.users),e._notFoundLabel=t=>e.hass.localize("ui.components.user-picker.no_match",{term:(0,u.qy)(w||(w=x`<b>‘${0}’</b>`),t)}),e}return(0,l.A)(t,e),(0,n.A)(t,[{key:"firstUpdated",value:function(e){(0,d.A)(t,"firstUpdated",this,3)([e]),this.users||this._fetchUsers()}},{key:"_fetchUsers",value:(i=(0,r.A)((0,a.A)().m((function e(){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,v.hU)(this.hass);case 1:this.users=e.v;case 2:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"render",value:function(){var e,t=null!==(e=this.placeholder)&&void 0!==e?e:this.hass.localize("ui.components.user-picker.user");return(0,u.qy)(M||(M=x`
      <ha-generic-picker
        .hass=${0}
        .autofocus=${0}
        .label=${0}
        .notFoundLabel=${0}
        .placeholder=${0}
        .value=${0}
        .getItems=${0}
        .valueRenderer=${0}
        .rowRenderer=${0}
        @value-changed=${0}
      >
      </ha-generic-picker>
    `),this.hass,this.autofocus,this.label,this._notFoundLabel,t,this.value,this._getItems,this._valueRenderer,this._rowRenderer,this._valueChanged)}},{key:"_valueChanged",value:function(e){var t=e.detail.value;this.value=t,(0,p.r)(this,"value-changed",{value:t}),(0,p.r)(this,"change")}}]);var i}(u.WF);(0,c.__decorate)([(0,h.MZ)({attribute:!1})],H.prototype,"hass",void 0),(0,c.__decorate)([(0,h.MZ)()],H.prototype,"label",void 0),(0,c.__decorate)([(0,h.MZ)()],H.prototype,"placeholder",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],H.prototype,"noUserLabel",void 0),(0,c.__decorate)([(0,h.MZ)()],H.prototype,"value",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],H.prototype,"users",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean})],H.prototype,"disabled",void 0),H=(0,c.__decorate)([(0,h.EM)("ha-user-picker")],H),t()}catch(V){t(V)}}))},31652:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),r=i(50264),o=i(94741),n=i(44734),s=i(56038),l=i(69683),d=i(6454),c=i(25460),u=(i(28706),i(2008),i(50113),i(74423),i(62062),i(54554),i(18111),i(22489),i(20116),i(61701),i(26099),i(62826)),h=i(96196),g=i(77845),p=i(58673),v=i(22786),_=i(92542),f=i(47268),m=(i(60733),i(53977)),y=e([m]);m=(y.then?(await y)():y)[0];var b,A,$,k,C=e=>e,w=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,l.A)(this,t,[].concat(a))).disabled=!1,e._notSelectedUsers=(0,v.A)(((e,t)=>t?null==e?void 0:e.filter((e=>!e.system_generated&&!t.includes(e.id))):null==e?void 0:e.filter((e=>!e.system_generated)))),e._notSelectedUsersAndSelected=(e,t,i)=>{var a=null==t?void 0:t.find((t=>t.id===e));return a?i?[].concat((0,o.A)(i),[a]):[a]:i},e}return(0,d.A)(t,e),(0,s.A)(t,[{key:"firstUpdated",value:function(e){(0,c.A)(t,"firstUpdated",this,3)([e]),this.users||this._fetchUsers()}},{key:"_fetchUsers",value:(g=(0,r.A)((0,a.A)().m((function e(){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,f.hU)(this.hass);case 1:this.users=e.v;case 2:return e.a(2)}}),e,this)}))),function(){return g.apply(this,arguments)})},{key:"render",value:function(){if(!this.hass||!this.users)return h.s6;var e=this._notSelectedUsers(this.users,this.value);return(0,h.qy)(b||(b=C`
      ${0}
      ${0}
      <div>
        <ha-user-picker
          .placeholder=${0}
          .hass=${0}
          .users=${0}
          .disabled=${0}
          @value-changed=${0}
        ></ha-user-picker>
      </div>
    `),this.label?(0,h.qy)(A||(A=C`<label>${0}</label>`),this.label):h.s6,(0,p.a)([e],(()=>{var t;return null===(t=this.value)||void 0===t?void 0:t.map(((t,i)=>(0,h.qy)($||($=C`
            <div>
              <ha-user-picker
                .placeholder=${0}
                .index=${0}
                .hass=${0}
                .value=${0}
                .users=${0}
                .disabled=${0}
                @value-changed=${0}
              ></ha-user-picker>
            </div>
          `),this.pickedUserLabel,i,this.hass,t,this._notSelectedUsersAndSelected(t,this.users,e),this.disabled,this._userChanged)))})),this.pickUserLabel||this.hass.localize("ui.components.user-picker.add_user"),this.hass,e,this.disabled||!(null!=e&&e.length),this._addUser)}},{key:"_currentUsers",get:function(){return this.value||[]}},{key:"_updateUsers",value:(u=(0,r.A)((0,a.A)().m((function e(t){return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:this.value=t,(0,_.r)(this,"value-changed",{value:t});case 1:return e.a(2)}}),e,this)}))),function(e){return u.apply(this,arguments)})},{key:"_userChanged",value:function(e){e.stopPropagation();var t=e.currentTarget.index,i=e.detail.value,a=(0,o.A)(this._currentUsers);i?a.splice(t,1,i):a.splice(t,1),this._updateUsers(a)}},{key:"_addUser",value:(i=(0,r.A)((0,a.A)().m((function e(t){var i,r;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:if(t.stopPropagation(),i=t.detail.value,t.currentTarget.value="",i){e.n=1;break}return e.a(2);case 1:if(!(r=this._currentUsers).includes(i)){e.n=2;break}return e.a(2);case 2:this._updateUsers([].concat((0,o.A)(r),[i]));case 3:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})}]);var i,u,g}(h.WF);w.styles=(0,h.AH)(k||(k=C`
    div {
      margin-top: 8px;
    }
  `)),(0,u.__decorate)([(0,g.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,u.__decorate)([(0,g.MZ)()],w.prototype,"label",void 0),(0,u.__decorate)([(0,g.MZ)({attribute:!1})],w.prototype,"value",void 0),(0,u.__decorate)([(0,g.MZ)({attribute:"picked-user-label"})],w.prototype,"pickedUserLabel",void 0),(0,u.__decorate)([(0,g.MZ)({attribute:"pick-user-label"})],w.prototype,"pickUserLabel",void 0),(0,u.__decorate)([(0,g.MZ)({attribute:!1})],w.prototype,"users",void 0),(0,u.__decorate)([(0,g.MZ)({type:Boolean})],w.prototype,"disabled",void 0),w=(0,u.__decorate)([(0,g.EM)("ha-users-picker")],w),t()}catch(M){t(M)}}))},47268:function(e,t,i){i.d(t,{_2:function(){return n},hU:function(){return o}});var a=i(61397),r=i(50264),o=(i(62062),i(44114),i(34782),i(18111),i(61701),i(26099),i(42762),function(){var e=(0,r.A)((0,a.A)().m((function e(t){return(0,a.A)().w((function(e){for(;;)if(0===e.n)return e.a(2,t.callWS({type:"config/auth/list"}))}),e)})));return function(t){return e.apply(this,arguments)}}()),n=e=>e?e.trim().split(" ").slice(0,3).map((e=>e.substring(0,1))).join(""):"?"},95836:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),r=i(56038),o=i(69683),n=i(6454),s=(i(52675),i(89463),i(28706),i(62826)),l=i(96196),d=i(77845),c=i(94333),u=i(51757),h=i(92542),g=(i(78740),i(23362)),p=i(80812),v=i(98995),_=i(39396),f=(i(13295),i(96608),e([g]));g=(f.then?(await f)():f)[0];var m,y,b,A,$,k,C,w=e=>e,M=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,r=new Array(i),n=0;n<i;n++)r[n]=arguments[n];return(e=(0,o.A)(this,t,[].concat(r))).disabled=!1,e.yamlMode=!1,e.uiSupported=!1,e.inSidebar=!1,e.showId=!1,e}return(0,n.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e=(0,v.H4)(this.trigger)?"list":this.trigger.trigger,t=this.yamlMode||!this.uiSupported,i="id"in this.trigger||this.showId;return(0,l.qy)(m||(m=w`
      <div
        class=${0}
      >
        ${0}
      </div>
    `),(0,c.H)({"card-content":!0,disabled:this.disabled||"enabled"in this.trigger&&!1===this.trigger.enabled&&!this.yamlMode,yaml:t,card:!this.inSidebar}),t?(0,l.qy)(y||(y=w`
              ${0}
              <ha-yaml-editor
                .hass=${0}
                .defaultValue=${0}
                .readOnly=${0}
                @value-changed=${0}
              ></ha-yaml-editor>
            `),this.uiSupported?l.s6:(0,l.qy)(b||(b=w`
                    <ha-automation-editor-warning
                      .alertTitle=${0}
                      .localize=${0}
                    ></ha-automation-editor-warning>
                  `),this.hass.localize("ui.panel.config.automation.editor.triggers.unsupported_platform",{platform:e}),this.hass.localize),this.hass,this.trigger,this.disabled,this._onYamlChange):(0,l.qy)(A||(A=w`
              ${0}
              <div @value-changed=${0}>
                ${0}
              </div>
            `),i&&!(0,v.H4)(this.trigger)?(0,l.qy)($||($=w`
                    <ha-textfield
                      .label=${0}
                      .value=${0}
                      .disabled=${0}
                      @change=${0}
                    ></ha-textfield>
                  `),this.hass.localize("ui.panel.config.automation.editor.triggers.id"),this.trigger.id||"",this.disabled,this._idChanged):l.s6,this._onUiChanged,this.description?(0,l.qy)(k||(k=w`<ha-automation-trigger-platform
                      .hass=${0}
                      .trigger=${0}
                      .description=${0}
                      .disabled=${0}
                    ></ha-automation-trigger-platform>`),this.hass,this.trigger,this.description,this.disabled):(0,u._)(`ha-automation-trigger-${e}`,{hass:this.hass,trigger:this.trigger,disabled:this.disabled})))}},{key:"_idChanged",value:function(e){var t;if(!(0,v.H4)(this.trigger)){var i=e.target.value;if(i!==(null!==(t=this.trigger.id)&&void 0!==t?t:"")){var a=Object.assign({},this.trigger);i?a.id=i:delete a.id,(0,h.r)(this,"value-changed",{value:a})}}}},{key:"_onYamlChange",value:function(e){e.stopPropagation(),e.detail.isValid&&(0,h.r)(this,this.inSidebar?"yaml-changed":"value-changed",{value:(0,p.vO)(e.detail.value)})}},{key:"_onUiChanged",value:function(e){if(!(0,v.H4)(this.trigger)){e.stopPropagation();var t=Object.assign(Object.assign({},this.trigger.alias?{alias:this.trigger.alias}:{}),e.detail.value);(0,h.r)(this,"value-changed",{value:t})}}}],[{key:"styles",get:function(){return[_.RF,(0,l.AH)(C||(C=w`
        .disabled {
          pointer-events: none;
        }

        .card-content.yaml {
          padding: 0 1px;
          border-top: 1px solid var(--divider-color);
          border-bottom: 1px solid var(--divider-color);
        }
        ha-textfield {
          display: block;
          margin-bottom: 24px;
        }
      `))]}}])}(l.WF);(0,s.__decorate)([(0,d.MZ)({attribute:!1})],M.prototype,"hass",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],M.prototype,"trigger",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean})],M.prototype,"disabled",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean,attribute:"yaml"})],M.prototype,"yamlMode",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean,attribute:"supported"})],M.prototype,"uiSupported",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean,attribute:"sidebar"})],M.prototype,"inSidebar",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean,attribute:"show-id"})],M.prototype,"showId",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],M.prototype,"description",void 0),(0,s.__decorate)([(0,d.P)("ha-yaml-editor")],M.prototype,"yamlEditor",void 0),M=(0,s.__decorate)([(0,d.EM)("ha-automation-trigger-editor")],M),t()}catch(x){t(x)}}))},46457:function(e,t,i){i.a(e,(async function(e,a){try{i.d(t,{P:function(){return pe}});var r=i(61397),o=i(50264),n=i(44734),s=i(56038),l=i(75864),d=i(69683),c=i(6454),u=i(25460),h=(i(28706),i(18111),i(13579),i(26099),i(62826)),g=i(16527),p=i(53289),v=i(96196),_=i(77845),f=i(94333),m=i(22786),y=i(55376),b=i(42256),A=i(92542),$=i(91737),k=i(55124),C=i(74522),w=i(91225),M=i(4657),x=i(40404),H=(i(17963),i(27639),i(95379),i(34811),i(60733),i(63419),i(32072),i(99892),i(60961),i(58103)),V=i(80812),L=i(53295),z=i(34485),Z=i(34972),O=i(98995),S=i(10234),q=i(98315),j=i(4848),T=(i(13295),i(36857)),E=i(95836),P=(i(18421),i(62472),i(61941)),U=i(72503),I=(i(21738),i(14822),i(31927)),B=(i(14674),i(55838),i(96608),i(24590),i(77461),i(93479),i(95669),i(70234)),F=(i(35215),i(35562)),W=i(36797),D=e([E,P,U,I,B,F,W,H,L]);[E,P,U,I,B,F,W,H,L]=D.then?(await D)():D;var R,K,Y,N,G,X,J,Q,ee,te,ie,ae,re,oe,ne,se,le,de,ce,ue,he=e=>e,ge="M6,2A4,4 0 0,1 10,6V8H14V6A4,4 0 0,1 18,2A4,4 0 0,1 22,6A4,4 0 0,1 18,10H16V14H18A4,4 0 0,1 22,18A4,4 0 0,1 18,22A4,4 0 0,1 14,18V16H10V18A4,4 0 0,1 6,22A4,4 0 0,1 2,18A4,4 0 0,1 6,14H8V10H6A4,4 0 0,1 2,6A4,4 0 0,1 6,2M16,18A2,2 0 0,0 18,20A2,2 0 0,0 20,18A2,2 0 0,0 18,16H16V18M14,10H10V14H14V10M6,16A2,2 0 0,0 4,18A2,2 0 0,0 6,20A2,2 0 0,0 8,18V16H6M8,6A2,2 0 0,0 6,4A2,2 0 0,0 4,6A2,2 0 0,0 6,8H8V6M18,8A2,2 0 0,0 20,6A2,2 0 0,0 18,4A2,2 0 0,0 16,6V8H18Z",pe=(e,t)=>{var i,a,r;t.stopPropagation();var o=null===(i=t.currentTarget)||void 0===i?void 0:i.name;if(o){var n,s=(null===(a=t.detail)||void 0===a?void 0:a.value)||(null===(r=t.currentTarget)||void 0===r?void 0:r.value);if((e.trigger[o]||"")!==s)void 0===s||""===s?delete(n=Object.assign({},e.trigger))[o]:n=Object.assign(Object.assign({},e.trigger),{},{[o]:s}),(0,A.r)(e,"value-changed",{value:n})}},ve=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),s=0;s<i;s++)a[s]=arguments[s];return(e=(0,d.A)(this,t,[].concat(a))).disabled=!1,e.optionsInSidebar=!1,e.sortSelected=!1,e._yamlMode=!1,e._triggerColor=!1,e._selected=!1,e.triggerDescriptions={},e.narrow=!1,e._doSubscribeTrigger=(0,x.s)((0,o.A)((0,r.A)().m((function t(){var i,a,o,n;return(0,r.A)().w((function(t){for(;;)switch(t.n){case 0:return a=5e3,o=e.trigger,e._triggerUnsub&&(e._triggerUnsub.then((e=>e())),e._triggerUnsub=void 0),t.n=1,(0,z.$)(e.hass,{triggers:o});case 1:if(t.v.triggers.valid&&e.trigger===o){t.n=2;break}return t.a(2);case 2:(n=(0,V.Dp)(e.hass,(t=>{void 0!==i?(clearTimeout(i),e._triggerColor=!e._triggerColor):e._triggerColor=!1,e._triggered=t,i=window.setTimeout((()=>{e._triggered=void 0,i=void 0}),a)}),o)).catch((()=>{e._triggerUnsub===n&&(e._triggerUnsub=void 0)})),e._triggerUnsub=n;case 3:return t.a(2)}}),t)}))),5e3),e._onDelete=()=>{(0,A.r)((0,l.A)(e),"value-changed",{value:null}),e._selected&&(0,A.r)((0,l.A)(e),"close-sidebar"),(0,j.P)((0,l.A)(e),{message:e.hass.localize("ui.common.successfully_deleted"),duration:4e3,action:{text:e.hass.localize("ui.common.undo"),action:()=>{(0,A.r)(window,"undo-change")}}})},e._onDisable=()=>{var t;if(!(0,O.H4)(e.trigger)){var i,a=!(null===(t=e.trigger.enabled)||void 0===t||t),r=Object.assign(Object.assign({},e.trigger),{},{enabled:a});if((0,A.r)((0,l.A)(e),"value-changed",{value:r}),e._selected&&e.optionsInSidebar&&e.openSidebar(r),e._yamlMode&&!e.optionsInSidebar)null===(i=e.triggerEditor)||void 0===i||null===(i=i.yamlEditor)||void 0===i||i.setValue(r)}},e._renameTrigger=(0,o.A)((0,r.A)().m((function t(){var i,a,o;return(0,r.A)().w((function(t){for(;;)switch(t.n){case 0:if(!(0,O.H4)(e.trigger)){t.n=1;break}return t.a(2);case 1:return t.n=2,(0,S.an)((0,l.A)(e),{title:e.hass.localize("ui.panel.config.automation.editor.triggers.change_alias"),inputLabel:e.hass.localize("ui.panel.config.automation.editor.triggers.alias"),inputType:"string",placeholder:(0,C.Z)((0,L.g)(e.trigger,e.hass,e._entityReg,!0)),defaultValue:e.trigger.alias,confirmText:e.hass.localize("ui.common.submit")});case 2:null!==(i=t.v)&&(a=Object.assign({},e.trigger),""===i?delete a.alias:a.alias=i,(0,A.r)((0,l.A)(e),"value-changed",{value:a}),e._selected&&e.optionsInSidebar?e.openSidebar(a):e._yamlMode&&(null===(o=e.triggerEditor)||void 0===o||null===(o=o.yamlEditor)||void 0===o||o.setValue(a)));case 3:return t.a(2)}}),t)}))),e._duplicateTrigger=()=>{(0,A.r)((0,l.A)(e),"duplicate")},e._insertAfter=t=>!(0,y.e)(t).some((e=>!(0,V.fo)(e)))&&((0,A.r)((0,l.A)(e),"insert-after",{value:t}),!0),e._copyTrigger=()=>{e._setClipboard(),(0,j.P)((0,l.A)(e),{message:e.hass.localize("ui.panel.config.automation.editor.triggers.copied_to_clipboard"),duration:2e3})},e._cutTrigger=()=>{e._setClipboard(),(0,A.r)((0,l.A)(e),"value-changed",{value:null}),e._selected&&(0,A.r)((0,l.A)(e),"close-sidebar"),(0,j.P)((0,l.A)(e),{message:e.hass.localize("ui.panel.config.automation.editor.triggers.cut_to_clipboard"),duration:2e3})},e._moveUp=()=>{(0,A.r)((0,l.A)(e),"move-up")},e._moveDown=()=>{(0,A.r)((0,l.A)(e),"move-down")},e._toggleYamlMode=t=>{e._yamlMode?e._switchUiMode():e._switchYamlMode(),e.optionsInSidebar?t&&e.openSidebar():e.expand()},e._getType=(0,m.A)(((e,t)=>(0,O.H4)(e)?"list":e.trigger in t?"platform":e.trigger)),e._uiSupported=(0,m.A)((e=>void 0!==customElements.get(`ha-automation-trigger-${e}`))),e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"selected",get:function(){return this._selected}},{key:"_renderOverflowLabel",value:function(e,t){return(0,v.qy)(R||(R=he`
      <div class="overflow-label">
        ${0}
        ${0}
      </div>
    `),e,this.optionsInSidebar&&!this.narrow?t||(0,v.qy)(K||(K=he`<span
              class="shortcut-placeholder ${0}"
            ></span>`),q.c?"mac":""):v.s6)}},{key:"_renderRow",value:function(){var e=this._getType(this.trigger,this.triggerDescriptions),t=this._uiSupported(e),i=this._yamlMode||!t;return(0,v.qy)(Y||(Y=he`
      ${0}
      <h3 slot="header">
        ${0}
      </h3>

      <slot name="icons" slot="icons"></slot>

      <ha-md-button-menu
        quick
        slot="icons"
        @click=${0}
        @keydown=${0}
        @closed=${0}
        positioning="fixed"
        anchor-corner="end-end"
        menu-corner="start-end"
      >
        <ha-icon-button
          slot="trigger"
          .label=${0}
          .path=${0}
        ></ha-icon-button>
        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
          ${0}
        </ha-md-menu-item>

        <ha-md-divider role="separator" tabindex="-1"></ha-md-divider>

        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon
            slot="start"
            .path=${0}
          ></ha-svg-icon>

          ${0}
        </ha-md-menu-item>

        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
          ${0}
        </ha-md-menu-item>

        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
          ${0}
        </ha-md-menu-item>

        ${0}

        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
          ${0}
        </ha-md-menu-item>

        <ha-md-divider role="separator" tabindex="-1"></ha-md-divider>

        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon
            slot="start"
            .path=${0}
          ></ha-svg-icon>

          ${0}
        </ha-md-menu-item>
        <ha-md-menu-item
          .clickAction=${0}
          class="warning"
          .disabled=${0}
        >
          <ha-svg-icon
            class="warning"
            slot="start"
            .path=${0}
          ></ha-svg-icon>
          ${0}
        </ha-md-menu-item>
      </ha-md-button-menu>
      ${0}
    `),"list"===e?(0,v.qy)(N||(N=he`<ha-svg-icon
            slot="leading-icon"
            class="trigger-icon"
            .path=${0}
          ></ha-svg-icon>`),H.S[e]):(0,v.qy)(G||(G=he`<ha-trigger-icon
            slot="leading-icon"
            .hass=${0}
            .trigger=${0}
          ></ha-trigger-icon>`),this.hass,this.trigger.trigger),(0,L.g)(this.trigger,this.hass,this._entityReg),$.C,k.d,k.d,this.hass.localize("ui.common.menu"),"M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z",this._renameTrigger,this.disabled||"list"===e,"M18,17H10.5L12.5,15H18M6,17V14.5L13.88,6.65C14.07,6.45 14.39,6.45 14.59,6.65L16.35,8.41C16.55,8.61 16.55,8.92 16.35,9.12L8.47,17M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.triggers.rename")),this._duplicateTrigger,this.disabled,"M16,8H14V11H11V13H14V16H16V13H19V11H16M2,12C2,9.21 3.64,6.8 6,5.68V3.5C2.5,4.76 0,8.09 0,12C0,15.91 2.5,19.24 6,20.5V18.32C3.64,17.2 2,14.79 2,12M15,3C10.04,3 6,7.04 6,12C6,16.96 10.04,21 15,21C19.96,21 24,16.96 24,12C24,7.04 19.96,3 15,3M15,19C11.14,19 8,15.86 8,12C8,8.14 11.14,5 15,5C18.86,5 22,8.14 22,12C22,15.86 18.86,19 15,19Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.actions.duplicate")),this._copyTrigger,this.disabled,"M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.triggers.copy"),(0,v.qy)(X||(X=he`<span class="shortcut">
              <span
                >${0}</span
              >
              <span>+</span>
              <span>C</span>
            </span>`),q.c?(0,v.qy)(J||(J=he`<ha-svg-icon
                      slot="start"
                      .path=${0}
                    ></ha-svg-icon>`),ge):this.hass.localize("ui.panel.config.automation.editor.ctrl"))),this._cutTrigger,this.disabled,"M19,3L13,9L15,11L22,4V3M12,12.5A0.5,0.5 0 0,1 11.5,12A0.5,0.5 0 0,1 12,11.5A0.5,0.5 0 0,1 12.5,12A0.5,0.5 0 0,1 12,12.5M6,20A2,2 0 0,1 4,18C4,16.89 4.9,16 6,16A2,2 0 0,1 8,18C8,19.11 7.1,20 6,20M6,8A2,2 0 0,1 4,6C4,4.89 4.9,4 6,4A2,2 0 0,1 8,6C8,7.11 7.1,8 6,8M9.64,7.64C9.87,7.14 10,6.59 10,6A4,4 0 0,0 6,2A4,4 0 0,0 2,6A4,4 0 0,0 6,10C6.59,10 7.14,9.87 7.64,9.64L10,12L7.64,14.36C7.14,14.13 6.59,14 6,14A4,4 0 0,0 2,18A4,4 0 0,0 6,22A4,4 0 0,0 10,18C10,17.41 9.87,16.86 9.64,16.36L12,14L19,21H22V20L9.64,7.64Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.triggers.cut"),(0,v.qy)(Q||(Q=he`<span class="shortcut">
              <span
                >${0}</span
              >
              <span>+</span>
              <span>X</span>
            </span>`),q.c?(0,v.qy)(ee||(ee=he`<ha-svg-icon
                      slot="start"
                      .path=${0}
                    ></ha-svg-icon>`),ge):this.hass.localize("ui.panel.config.automation.editor.ctrl"))),this.optionsInSidebar?v.s6:(0,v.qy)(te||(te=he`
              <ha-md-menu-item
                .clickAction=${0}
                .disabled=${0}
              >
                ${0}
                <ha-svg-icon slot="start" .path=${0}></ha-svg-icon
              ></ha-md-menu-item>
              <ha-md-menu-item
                .clickAction=${0}
                .disabled=${0}
              >
                ${0}
                <ha-svg-icon slot="start" .path=${0}></ha-svg-icon
              ></ha-md-menu-item>
            `),this._moveUp,this.disabled||!!this.first,this.hass.localize("ui.panel.config.automation.editor.move_up"),"M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z",this._moveDown,this.disabled||!!this.last,this.hass.localize("ui.panel.config.automation.editor.move_down"),"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z"),this._toggleYamlMode,!t||!!this._warnings,"M3 6V8H14V6H3M3 10V12H14V10H3M20 10.1C19.9 10.1 19.7 10.2 19.6 10.3L18.6 11.3L20.7 13.4L21.7 12.4C21.9 12.2 21.9 11.8 21.7 11.6L20.4 10.3C20.3 10.2 20.2 10.1 20 10.1M18.1 11.9L12 17.9V20H14.1L20.2 13.9L18.1 11.9M3 14V16H10V14H3Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.edit_"+(i?"ui":"yaml"))),this._onDisable,this.disabled||"list"===e,"enabled"in this.trigger&&!1===this.trigger.enabled?"M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M10,16.5L16,12L10,7.5V16.5Z":"M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4M9,9V15H15V9",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.actions."+("enabled"in this.trigger&&!1===this.trigger.enabled?"enable":"disable"))),this._onDelete,this.disabled,"M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.actions.delete"),(0,v.qy)(ie||(ie=he`<span class="shortcut">
              <span
                >${0}</span
              >
              <span>+</span>
              <span
                >${0}</span
              >
            </span>`),q.c?(0,v.qy)(ae||(ae=he`<ha-svg-icon
                      slot="start"
                      .path=${0}
                    ></ha-svg-icon>`),ge):this.hass.localize("ui.panel.config.automation.editor.ctrl"),this.hass.localize("ui.panel.config.automation.editor.del"))),this.optionsInSidebar?v.s6:(0,v.qy)(re||(re=he`${0}
            <ha-automation-trigger-editor
              .hass=${0}
              .trigger=${0}
              .description=${0}
              .disabled=${0}
              .yamlMode=${0}
              .uiSupported=${0}
              @ui-mode-not-available=${0}
            ></ha-automation-trigger-editor>`),this._warnings?(0,v.qy)(oe||(oe=he`<ha-automation-editor-warning
                  .localize=${0}
                  .warnings=${0}
                >
                </ha-automation-editor-warning>`),this.hass.localize,this._warnings):v.s6,this.hass,this.trigger,"trigger"in this.trigger?this.triggerDescriptions[this.trigger.trigger]:void 0,this.disabled,this._yamlMode,t,this._handleUiModeNotAvailable))}},{key:"render",value:function(){return this.trigger?(0,v.qy)(ne||(ne=he`
      <ha-card outlined class=${0}>
        ${0}
        ${0}
        <div
          class="triggered ${0}"
          @click=${0}
        >
          ${0}
          <ha-svg-icon .path=${0}></ha-svg-icon>
        </div>
      </ha-card>
    `),this._selected?"selected":"","enabled"in this.trigger&&!1===this.trigger.enabled?(0,v.qy)(se||(se=he`
              <div class="disabled-bar">
                ${0}
              </div>
            `),this.hass.localize("ui.panel.config.automation.editor.actions.disabled")):v.s6,this.optionsInSidebar?(0,v.qy)(le||(le=he`<ha-automation-row
              .disabled=${0}
              .selected=${0}
              .highlight=${0}
              .sortSelected=${0}
              @click=${0}
              >${0}${0}</ha-automation-row
            >`),"enabled"in this.trigger&&!1===this.trigger.enabled,this._selected,this.highlight,this.sortSelected,this._toggleSidebar,this._selected?"selected":v.s6,this._renderRow()):(0,v.qy)(de||(de=he`
              <ha-expansion-panel left-chevron>
                ${0}
              </ha-expansion-panel>
            `),this._renderRow()),(0,f.H)({active:void 0!==this._triggered,accent:this._triggerColor}),this._showTriggeredInfo,this.hass.localize("ui.panel.config.automation.editor.triggers.triggered"),"M13,9H11V7H13M13,17H11V11H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"):v.s6}},{key:"willUpdate",value:function(e){e.has("yamlMode")&&(this._warnings=void 0)}},{key:"updated",value:function(e){(0,u.A)(t,"updated",this,3)([e]),e.has("trigger")&&this._subscribeTrigger()}},{key:"connectedCallback",value:function(){(0,u.A)(t,"connectedCallback",this,3)([]),this.hasUpdated&&this.trigger&&this._subscribeTrigger()}},{key:"disconnectedCallback",value:function(){(0,u.A)(t,"disconnectedCallback",this,3)([]),this._triggerUnsub&&(this._triggerUnsub.then((e=>e())),this._triggerUnsub=void 0),this._doSubscribeTrigger.cancel()}},{key:"_subscribeTrigger",value:function(){this._triggerUnsub&&(this._triggerUnsub.then((e=>e())),this._triggerUnsub=void 0),this._doSubscribeTrigger()}},{key:"_handleUiModeNotAvailable",value:function(e){this._warnings=(0,w._)(this.hass,e.detail).warnings,this._yamlMode||(this._yamlMode=!0)}},{key:"_toggleSidebar",value:function(e){null==e||e.stopPropagation(),this._selected?(0,A.r)(this,"request-close-sidebar"):this.openSidebar()}},{key:"openSidebar",value:function(e){e=e||this.trigger,(0,A.r)(this,"open-sidebar",{save:e=>{(0,A.r)(this,"value-changed",{value:e})},close:e=>{this._selected=!1,(0,A.r)(this,"close-sidebar"),e&&this.focus()},rename:()=>{this._renameTrigger()},toggleYamlMode:()=>{this._toggleYamlMode(),this.openSidebar()},disable:this._onDisable,delete:this._onDelete,copy:this._copyTrigger,duplicate:this._duplicateTrigger,cut:this._cutTrigger,insertAfter:this._insertAfter,config:e,uiSupported:this._uiSupported(this._getType(e,this.triggerDescriptions)),description:"trigger"in e?this.triggerDescriptions[e.trigger]:void 0,yamlMode:this._yamlMode}),this._selected=!0,this.narrow&&window.setTimeout((()=>{this.scrollIntoView({block:"start",behavior:"smooth"})}),180)}},{key:"_setClipboard",value:function(){this._clipboard=Object.assign(Object.assign({},this._clipboard),{},{trigger:this.trigger}),(0,M.l)((0,p.Bh)(this.trigger))}},{key:"_switchUiMode",value:function(){this._yamlMode=!1}},{key:"_switchYamlMode",value:function(){this._yamlMode=!0}},{key:"_showTriggeredInfo",value:function(){(0,S.K$)(this,{title:this.hass.localize("ui.panel.config.automation.editor.triggers.triggering_event_detail"),text:(0,v.qy)(ce||(ce=he`
        <ha-yaml-editor
          read-only
          disable-fullscreen
          .hass=${0}
          .defaultValue=${0}
        ></ha-yaml-editor>
      `),this.hass,this._triggered)})}},{key:"expand",value:function(){this.updateComplete.then((()=>{this.shadowRoot.querySelector("ha-expansion-panel").expanded=!0}))}},{key:"focus",value:function(){var e;null===(e=this._automationRowElement)||void 0===e||e.focus()}}],[{key:"styles",get:function(){return[T.bH,T.Lt,(0,v.AH)(ue||(ue=he`
        .triggered {
          cursor: pointer;
          position: absolute;
          top: 0px;
          right: 0px;
          left: 0px;
          text-transform: uppercase;
          font-size: var(--ha-font-size-m);
          font-weight: var(--ha-font-weight-bold);
          background-color: var(--primary-color);
          color: var(--text-primary-color);
          max-height: 0px;
          overflow: hidden;
          transition: max-height 0.3s;
          text-align: center;
          border-top-right-radius: var(
            --ha-card-border-radius,
            var(--ha-border-radius-lg)
          );
          border-top-left-radius: var(
            --ha-card-border-radius,
            var(--ha-border-radius-lg)
          );
          display: flex;
          justify-content: center;
          align-items: center;
          gap: var(--ha-space-1);
          line-height: 1;
          padding: 0;
        }
        .triggered ha-svg-icon {
          --mdc-icon-size: 16px;
        }

        .triggered.active {
          max-height: 100px;
          padding: 4px;
        }
        .triggered:hover {
          opacity: 0.8;
        }
        .triggered.accent {
          background-color: var(--accent-color);
          color: var(--text-accent-color, var(--text-primary-color));
        }
      `))]}}])}(v.WF);(0,h.__decorate)([(0,_.MZ)({attribute:!1})],ve.prototype,"hass",void 0),(0,h.__decorate)([(0,_.MZ)({attribute:!1})],ve.prototype,"trigger",void 0),(0,h.__decorate)([(0,_.MZ)({type:Boolean})],ve.prototype,"disabled",void 0),(0,h.__decorate)([(0,_.MZ)({type:Boolean})],ve.prototype,"first",void 0),(0,h.__decorate)([(0,_.MZ)({type:Boolean})],ve.prototype,"last",void 0),(0,h.__decorate)([(0,_.MZ)({type:Boolean})],ve.prototype,"highlight",void 0),(0,h.__decorate)([(0,_.MZ)({type:Boolean,attribute:"sidebar"})],ve.prototype,"optionsInSidebar",void 0),(0,h.__decorate)([(0,_.MZ)({type:Boolean,attribute:"sort-selected"})],ve.prototype,"sortSelected",void 0),(0,h.__decorate)([(0,_.wk)()],ve.prototype,"_yamlMode",void 0),(0,h.__decorate)([(0,_.wk)()],ve.prototype,"_triggered",void 0),(0,h.__decorate)([(0,_.wk)()],ve.prototype,"_triggerColor",void 0),(0,h.__decorate)([(0,_.wk)()],ve.prototype,"_selected",void 0),(0,h.__decorate)([(0,_.wk)()],ve.prototype,"_warnings",void 0),(0,h.__decorate)([(0,_.MZ)({attribute:!1})],ve.prototype,"triggerDescriptions",void 0),(0,h.__decorate)([(0,_.MZ)({type:Boolean})],ve.prototype,"narrow",void 0),(0,h.__decorate)([(0,_.P)("ha-automation-trigger-editor")],ve.prototype,"triggerEditor",void 0),(0,h.__decorate)([(0,_.P)("ha-automation-row")],ve.prototype,"_automationRowElement",void 0),(0,h.__decorate)([(0,b.I)({key:"automationClipboard",state:!1,subscribe:!0,storage:"sessionStorage"})],ve.prototype,"_clipboard",void 0),(0,h.__decorate)([(0,_.wk)(),(0,g.Fg)({context:Z.ih,subscribe:!0})],ve.prototype,"_entityReg",void 0),ve=(0,h.__decorate)([(0,_.EM)("ha-automation-trigger-row")],ve),a()}catch(_e){a(_e)}}))},82720:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),r=i(94741),o=i(50264),n=i(44734),s=i(56038),l=i(75864),d=i(69683),c=i(6454),u=i(25460),h=(i(28706),i(2008),i(74423),i(23792),i(34782),i(54554),i(71658),i(18111),i(22489),i(7588),i(26099),i(38781),i(73772),i(23500),i(62953),i(62826)),g=i(34271),p=i(96196),v=i(77845),_=i(4937),f=i(55376),m=i(42256),y=i(92542),b=i(55124),A=i(99034),$=i(89473),k=(i(16857),i(63801),i(60961),i(80812)),C=i(78991),w=i(98995),M=i(10085),x=i(78232),H=i(36857),V=i(46457),L=e([$,V]);[$,V]=L.then?(await L)():L;var z,Z,O,S=e=>e,q=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,d.A)(this,t,[].concat(a))).disabled=!1,e.narrow=!1,e.optionsInSidebar=!1,e.root=!1,e._focusLastTriggerOnChange=!1,e._triggerKeys=new WeakMap,e._triggerDescriptions={},e._newTriggersAndConditions=!1,e._addTrigger=(t,i)=>{var a;if(t===x.u)a=e.triggers.concat((0,g.A)(e._clipboard.trigger));else if((0,k.Q)(t))a=e.triggers.concat({trigger:(0,k.Dt)(t),target:i});else{var r=t,o=customElements.get(`ha-automation-trigger-${r}`);a=e.triggers.concat(Object.assign({},o.defaultConfig))}e._focusLastTriggerOnChange=!0,(0,y.r)((0,l.A)(e),"value-changed",{value:a})},e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"disconnectedCallback",value:function(){(0,u.A)(t,"disconnectedCallback",this,3)([]),this._unsubscribe()}},{key:"hassSubscribe",value:function(){return[(0,C.CO)(this.hass.connection,"automation","new_triggers_conditions",(e=>{this._newTriggersAndConditions=e.enabled}))]}},{key:"_subscribeDescriptions",value:function(){this._unsubscribe(),this._triggerDescriptions={},this._unsub=(0,w.Wv)(this.hass,(e=>{this._triggerDescriptions=Object.assign(Object.assign({},this._triggerDescriptions),e)}))}},{key:"_unsubscribe",value:function(){this._unsub&&(this._unsub.then((e=>e())),this._unsub=void 0)}},{key:"willUpdate",value:function(e){(0,u.A)(t,"willUpdate",this,3)([e]),e.has("_newTriggersAndConditions")&&this._subscribeDescriptions()}},{key:"firstUpdated",value:function(e){(0,u.A)(t,"firstUpdated",this,3)([e]),this.hass.loadBackendTranslation("triggers")}},{key:"render",value:function(){return(0,p.qy)(z||(z=S`
      <ha-sortable
        handle-selector=".handle"
        draggable-selector="ha-automation-trigger-row"
        .disabled=${0}
        group="triggers"
        invert-swap
        @item-moved=${0}
        @item-added=${0}
        @item-removed=${0}
      >
        <div class="rows ${0}">
          ${0}
          <div class="buttons">
            <ha-button
              .disabled=${0}
              @click=${0}
              .appearance=${0}
              .size=${0}
            >
              ${0}
              <ha-svg-icon .path=${0} slot="start"></ha-svg-icon>
            </ha-button>
          </div>
        </div>
      </ha-sortable>
    `),this.disabled,this._triggerMoved,this._triggerAdded,this._triggerRemoved,this.optionsInSidebar?"":"no-sidebar",(0,_.u)(this.triggers,(e=>this._getKey(e)),((e,t)=>{var i;return(0,p.qy)(Z||(Z=S`
              <ha-automation-trigger-row
                .sortableData=${0}
                .index=${0}
                .first=${0}
                .last=${0}
                .trigger=${0}
                .triggerDescriptions=${0}
                @duplicate=${0}
                @insert-after=${0}
                @move-down=${0}
                @move-up=${0}
                @value-changed=${0}
                .hass=${0}
                .disabled=${0}
                .narrow=${0}
                .highlight=${0}
                .optionsInSidebar=${0}
                .sortSelected=${0}
                @stop-sort-selection=${0}
              >
                ${0}
              </ha-automation-trigger-row>
            `),e,t,0===t,t===this.triggers.length-1,e,this._triggerDescriptions,this._duplicateTrigger,this._insertAfter,this._moveDown,this._moveUp,this._triggerChanged,this.hass,this.disabled,this.narrow,null===(i=this.highlightedTriggers)||void 0===i?void 0:i.includes(e),this.optionsInSidebar,this._rowSortSelected===t,this._stopSortSelection,this.disabled?p.s6:(0,p.qy)(O||(O=S`
                      <div
                        tabindex="0"
                        class="handle ${0}"
                        slot="icons"
                        @keydown=${0}
                        @click=${0}
                        .index=${0}
                      >
                        <ha-svg-icon
                          .path=${0}
                        ></ha-svg-icon>
                      </div>
                    `),this._rowSortSelected===t?"active":"",this._handleDragKeydown,b.d,t,"M21 11H3V9H21V11M21 13H3V15H21V13Z"))})),this.disabled,this._addTriggerDialog,this.root?"accent":"filled",this.root?"medium":"small",this.hass.localize("ui.panel.config.automation.editor.triggers.add"),"M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z")}},{key:"_addTriggerDialog",value:function(){var e,t;this.narrow&&(0,y.r)(this,"request-close-sidebar"),(0,x.g)(this,{type:"trigger",add:this._addTrigger,clipboardItem:null!==(e=this._clipboard)&&void 0!==e&&e.trigger?(0,w.H4)(this._clipboard.trigger)?"list":null===(t=this._clipboard)||void 0===t||null===(t=t.trigger)||void 0===t?void 0:t.trigger:void 0})}},{key:"updated",value:function(e){if((0,u.A)(t,"updated",this,3)([e]),e.has("triggers")&&(this._focusLastTriggerOnChange||void 0!==this._focusTriggerIndexOnChange)){var i=this.shadowRoot.querySelector("ha-automation-trigger-row:"+(this._focusLastTriggerOnChange?"last-of-type":`nth-of-type(${this._focusTriggerIndexOnChange+1})`));this._focusLastTriggerOnChange=!1,this._focusTriggerIndexOnChange=void 0,i.updateComplete.then((()=>{this.optionsInSidebar?(i.openSidebar(),this.narrow&&i.scrollIntoView({block:"start",behavior:"smooth"})):(i.expand(),i.focus())}))}}},{key:"expandAll",value:function(){this.shadowRoot.querySelectorAll("ha-automation-trigger-row").forEach((e=>{e.expand()}))}},{key:"_getKey",value:function(e){return this._triggerKeys.has(e)||this._triggerKeys.set(e,Math.random().toString()),this._triggerKeys.get(e)}},{key:"_moveUp",value:function(e){e.stopPropagation();var t=e.target.index;if(!e.target.first){var i=t-1;this._move(t,i),this._rowSortSelected===t&&(this._rowSortSelected=i),e.target.focus()}}},{key:"_moveDown",value:function(e){e.stopPropagation();var t=e.target.index;if(!e.target.last){var i=t+1;this._move(t,i),this._rowSortSelected===t&&(this._rowSortSelected=i),e.target.focus()}}},{key:"_move",value:function(e,t){var i=this.triggers.concat(),a=i.splice(e,1)[0];i.splice(t,0,a),this.triggers=i,(0,y.r)(this,"value-changed",{value:i})}},{key:"_triggerMoved",value:function(e){e.stopPropagation();var t=e.detail,i=t.oldIndex,a=t.newIndex;this._move(i,a)}},{key:"_triggerAdded",value:(h=(0,o.A)((0,a.A)().m((function e(t){var i,o,n,s,l,d;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return t.stopPropagation(),i=t.detail,o=i.index,n=i.data,s=t.detail.item,l=s.selected,d=[].concat((0,r.A)(this.triggers.slice(0,o)),[n],(0,r.A)(this.triggers.slice(o))),this.triggers=d,l&&(this._focusTriggerIndexOnChange=1===d.length?0:o),e.n=1,(0,A.E)();case 1:this.triggers!==d&&(d=[].concat((0,r.A)(this.triggers.slice(0,o)),[n],(0,r.A)(this.triggers.slice(o))),l&&(this._focusTriggerIndexOnChange=1===d.length?0:o)),(0,y.r)(this,"value-changed",{value:d});case 2:return e.a(2)}}),e,this)}))),function(e){return h.apply(this,arguments)})},{key:"_triggerRemoved",value:(i=(0,o.A)((0,a.A)().m((function e(t){var i,r,o;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return t.stopPropagation(),i=t.detail.index,r=this.triggers[i],this.triggers=this.triggers.filter((e=>e!==r)),e.n=1,(0,A.E)();case 1:o=this.triggers.filter((e=>e!==r)),(0,y.r)(this,"value-changed",{value:o});case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_triggerChanged",value:function(e){e.stopPropagation();var t=(0,r.A)(this.triggers),i=e.detail.value,a=e.target.index;if(null===i)t.splice(a,1);else{var o=this._getKey(t[a]);this._triggerKeys.set(i,o),t[a]=i}(0,y.r)(this,"value-changed",{value:t})}},{key:"_duplicateTrigger",value:function(e){e.stopPropagation();var t=e.target.index;(0,y.r)(this,"value-changed",{value:this.triggers.toSpliced(t+1,0,(0,g.A)(this.triggers[t]))})}},{key:"_insertAfter",value:function(e){var t;e.stopPropagation();var i=e.target.index,a=(0,f.e)(e.detail.value);this.highlightedTriggers=a,(0,y.r)(this,"value-changed",{value:(t=this.triggers).toSpliced.apply(t,[i+1,0].concat((0,r.A)(a)))})}},{key:"_handleDragKeydown",value:function(e){"Enter"!==e.key&&" "!==e.key||(e.stopPropagation(),this._rowSortSelected=void 0===this._rowSortSelected?e.target.index:void 0)}},{key:"_stopSortSelection",value:function(){this._rowSortSelected=void 0}}]);var i,h}((0,M.E)(p.WF));q.styles=H.Ju,(0,h.__decorate)([(0,v.MZ)({attribute:!1})],q.prototype,"hass",void 0),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],q.prototype,"triggers",void 0),(0,h.__decorate)([(0,v.MZ)({attribute:!1})],q.prototype,"highlightedTriggers",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],q.prototype,"disabled",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],q.prototype,"narrow",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean,attribute:"sidebar"})],q.prototype,"optionsInSidebar",void 0),(0,h.__decorate)([(0,v.MZ)({type:Boolean})],q.prototype,"root",void 0),(0,h.__decorate)([(0,v.wk)()],q.prototype,"_rowSortSelected",void 0),(0,h.__decorate)([(0,v.wk)(),(0,m.I)({key:"automationClipboard",state:!0,subscribe:!0,storage:"sessionStorage"})],q.prototype,"_clipboard",void 0),(0,h.__decorate)([(0,v.wk)()],q.prototype,"_triggerDescriptions",void 0),(0,h.__decorate)([(0,v.wk)()],q.prototype,"_newTriggersAndConditions",void 0),q=(0,h.__decorate)([(0,v.EM)("ha-automation-trigger")],q),t()}catch(j){t(j)}}))},18421:function(e,t,i){var a,r=i(44734),o=i(56038),n=i(69683),s=i(6454),l=(i(28706),i(62826)),d=i(96196),c=i(77845),u=i(22786),h=i(92542),g=(i(91120),i(68006)),p=e=>e,v=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,n.A)(this,t,[].concat(a))).disabled=!1,e._schema=(0,u.A)((e=>[{name:"entity_id",required:!0,selector:{entity:{domain:"calendar"}}},{name:"event",type:"select",required:!0,options:[["start",e("ui.panel.config.automation.editor.triggers.type.calendar.start")],["end",e("ui.panel.config.automation.editor.triggers.type.calendar.end")]]},{name:"offset",required:!0,selector:{duration:{}}},{name:"offset_type",type:"select",required:!0,options:[["before",e("ui.panel.config.automation.editor.triggers.type.calendar.before")],["after",e("ui.panel.config.automation.editor.triggers.type.calendar.after")]]}])),e._computeLabelCallback=t=>{switch(t.name){case"entity_id":return e.hass.localize("ui.components.entity.entity-picker.entity");case"event":return e.hass.localize("ui.panel.config.automation.editor.triggers.type.calendar.event")}return""},e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){var e=this._schema(this.hass.localize),t=this.trigger.offset,i=(0,g.z)(t),r="after";("object"==typeof t&&i.hours<0||"string"==typeof t&&t.startsWith("-"))&&(i.hours=Math.abs(i.hours),r="before");var o=Object.assign(Object.assign({},this.trigger),{},{offset:i,offset_type:r});return(0,d.qy)(a||(a=p`
      <ha-form
        .schema=${0}
        .data=${0}
        .hass=${0}
        .disabled=${0}
        .computeLabel=${0}
        @value-changed=${0}
      ></ha-form>
    `),e,o,this.hass,this.disabled,this._computeLabelCallback,this._valueChanged)}},{key:"_valueChanged",value:function(e){var t,i,a;e.stopPropagation();var r=e.detail.value.offset,o="before"===e.detail.value.offset_type?"-":"",n=Object.assign(Object.assign({},e.detail.value),{},{offset:`${o}${null!==(t=r.hours)&&void 0!==t?t:0}:${null!==(i=r.minutes)&&void 0!==i?i:0}:${null!==(a=r.seconds)&&void 0!==a?a:0}`});delete n.offset_type,(0,h.r)(this,"value-changed",{value:n})}}],[{key:"defaultConfig",get:function(){return{trigger:"calendar",entity_id:"",event:"start",offset:"0"}}}])}(d.WF);(0,l.__decorate)([(0,c.MZ)({attribute:!1})],v.prototype,"hass",void 0),(0,l.__decorate)([(0,c.MZ)({attribute:!1})],v.prototype,"trigger",void 0),(0,l.__decorate)([(0,c.MZ)({type:Boolean})],v.prototype,"disabled",void 0),v=(0,l.__decorate)([(0,c.EM)("ha-automation-trigger-calendar")],v)},62472:function(e,t,i){var a,r,o,n=i(61397),s=i(50264),l=i(94741),d=i(44734),c=i(56038),u=i(69683),h=i(6454),g=(i(28706),i(62062),i(54554),i(18111),i(61701),i(26099),i(62826)),p=i(96196),v=i(77845),_=i(55376),f=i(92542),m=(i(78740),i(60733),i(10234)),y=e=>e,b="^[^.。,，?¿？؟!！;；:：]+$",A=function(e){function t(){var e;(0,d.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,u.A)(this,t,[].concat(a))).disabled=!1,e}return(0,h.A)(t,e),(0,c.A)(t,[{key:"render",value:function(){var e=this.trigger.command,t=e?(0,_.e)(e):[];return(0,p.qy)(a||(a=y`${0}
      <ha-textfield
        class="flex-auto"
        id="option_input"
        .label=${0}
        .validationMessage=${0}
        autoValidate
        pattern=${0}
        @keydown=${0}
        @change=${0}
      ></ha-textfield>`),t.length?t.map(((e,t)=>(0,p.qy)(r||(r=y`
              <ha-textfield
                class="option"
                iconTrailing
                .index=${0}
                .value=${0}
                .validationMessage=${0}
                autoValidate
                validateOnInitialRender
                pattern=${0}
                @change=${0}
              >
                <ha-icon-button
                  @click=${0}
                  slot="trailingIcon"
                  .path=${0}
                ></ha-icon-button>
              </ha-textfield>
            `),t,e,this.hass.localize("ui.panel.config.automation.editor.triggers.type.conversation.no_punctuation"),b,this._updateOption,this._removeOption,"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"))):p.s6,this.hass.localize("ui.panel.config.automation.editor.triggers.type.conversation.add_sentence"),this.hass.localize("ui.panel.config.automation.editor.triggers.type.conversation.no_punctuation"),b,this._handleKeyAdd,this._addOption)}},{key:"_handleKeyAdd",value:function(e){e.stopPropagation(),"Enter"===e.key&&this._addOption()}},{key:"_addOption",value:function(){var e=this._optionInput;null!=e&&e.value&&((0,f.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{command:this.trigger.command.length?[].concat((0,l.A)(Array.isArray(this.trigger.command)?this.trigger.command:[this.trigger.command]),[e.value]):e.value})}),e.value="")}},{key:"_updateOption",value:(o=(0,s.A)((0,n.A)().m((function e(t){var i,a;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:i=t.target.index,(a=(0,l.A)(Array.isArray(this.trigger.command)?this.trigger.command:[this.trigger.command])).splice(i,1,t.target.value),(0,f.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{command:a})});case 1:return e.a(2)}}),e,this)}))),function(e){return o.apply(this,arguments)})},{key:"_removeOption",value:(i=(0,s.A)((0,n.A)().m((function e(t){var i,a;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:return i=t.target.parentElement.index,e.n=1,(0,m.dk)(this,{title:this.hass.localize("ui.panel.config.automation.editor.triggers.type.conversation.delete"),text:this.hass.localize("ui.panel.config.automation.editor.triggers.type.conversation.confirm_delete"),destructive:!0});case 1:if(e.v){e.n=2;break}return e.a(2);case 2:Array.isArray(this.trigger.command)?(a=(0,l.A)(this.trigger.command)).splice(i,1):a="",(0,f.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{command:a})});case 3:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})}],[{key:"defaultConfig",get:function(){return{trigger:"conversation",command:""}}}]);var i,o}(p.WF);A.styles=(0,p.AH)(o||(o=y`
    .layout {
      display: flex;
      flex-direction: row;
      flex-wrap: nowrap;
      align-items: center;
      justify-content: flex-start;
    }
    .option {
      margin-top: 4px;
    }
    ha-textfield {
      display: block;
      margin-bottom: 8px;
      --textfield-icon-trailing-padding: 0;
    }
    ha-textfield > ha-icon-button {
      position: relative;
      right: -8px;
      --mdc-icon-button-size: 36px;
      --mdc-icon-size: 20px;
      color: var(--secondary-text-color);
      inset-inline-start: initial;
      inset-inline-end: -8px;
      direction: var(--direction);
    }
    #option_input {
      margin-top: 8px;
    }
    .header {
      margin-top: 8px;
      margin-bottom: 8px;
    }
  `)),(0,g.__decorate)([(0,v.MZ)({attribute:!1})],A.prototype,"hass",void 0),(0,g.__decorate)([(0,v.MZ)({attribute:!1})],A.prototype,"trigger",void 0),(0,g.__decorate)([(0,v.MZ)({type:Boolean})],A.prototype,"disabled",void 0),(0,g.__decorate)([(0,v.P)("#option_input",!0)],A.prototype,"_optionInput",void 0),A=(0,g.__decorate)([(0,v.EM)("ha-automation-trigger-conversation")],A)},61941:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),r=i(50264),o=i(44734),n=i(56038),s=i(69683),l=i(6454),d=(i(16280),i(28706),i(18111),i(7588),i(26099),i(23500),i(62826)),c=i(16527),u=i(96196),h=i(77845),g=i(22786),p=i(92542),v=i(38852),_=i(60977),f=(i(25854),i(91120),i(23442)),m=i(34972),y=i(74687),b=e([_]);_=(b.then?(await b)():b)[0];var A,$,k,C=e=>e,w=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(a))).disabled=!1,e._extraFieldsData=(0,g.A)(((e,t)=>{var i=(0,f.$)(t.extra_fields);return t.extra_fields.forEach((t=>{void 0!==e[t.name]&&(i[t.name]=e[t.name])})),i})),e}return(0,l.A)(t,e),(0,n.A)(t,[{key:"shouldUpdate",value:function(e){return!e.has("trigger")||(!this.trigger.device_id||this.trigger.device_id in this.hass.devices||((0,p.r)(this,"ui-mode-not-available",Error(this.hass.localize("ui.panel.config.automation.editor.edit_unknown_device"))),!1))}},{key:"render",value:function(){var e,t=this._deviceId||this.trigger.device_id;return(0,u.qy)(A||(A=C`
      <ha-device-picker
        .value=${0}
        @value-changed=${0}
        .hass=${0}
        .disabled=${0}
        .label=${0}
      ></ha-device-picker>
      <ha-device-trigger-picker
        .value=${0}
        .deviceId=${0}
        @value-changed=${0}
        .hass=${0}
        .disabled=${0}
        .label=${0}
      ></ha-device-trigger-picker>
      ${0}
    `),t,this._devicePicked,this.hass,this.disabled,this.hass.localize("ui.panel.config.automation.editor.triggers.type.device.label"),this.trigger,t,this._deviceTriggerPicked,this.hass,this.disabled,this.hass.localize("ui.panel.config.automation.editor.triggers.type.device.trigger"),null!==(e=this._capabilities)&&void 0!==e&&e.extra_fields?(0,u.qy)($||($=C`
            <ha-form
              .hass=${0}
              .data=${0}
              .schema=${0}
              .disabled=${0}
              .computeLabel=${0}
              .computeHelper=${0}
              @value-changed=${0}
            ></ha-form>
          `),this.hass,this._extraFieldsData(this.trigger,this._capabilities),this._capabilities.extra_fields,this.disabled,(0,y.T_)(this.hass,this.trigger),(0,y.TH)(this.hass,this.trigger),this._extraFieldsChanged):"")}},{key:"firstUpdated",value:function(){this.hass.loadBackendTranslation("device_automation"),this._capabilities||this._getCapabilities(),this.trigger&&(this._origTrigger=this.trigger)}},{key:"updated",value:function(e){if(e.has("trigger")){var t=e.get("trigger");t&&!(0,y.Po)(this._entityReg,t,this.trigger)&&this._getCapabilities()}}},{key:"_getCapabilities",value:(i=(0,r.A)((0,a.A)().m((function e(){var t,i,r;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:if(!(t=this.trigger).domain){e.n=2;break}return e.n=1,(0,y.TB)(this.hass,t);case 1:r=e.v,e.n=3;break;case 2:r=void 0;case 3:this._capabilities=r,this._capabilities&&(i=Object.assign(Object.assign({},this.trigger),this._extraFieldsData(this.trigger,this._capabilities)),(0,v.b)(this.trigger,i)||(0,p.r)(this,"value-changed",{value:i}));case 4:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_devicePicked",value:function(e){e.stopPropagation(),this._deviceId=e.target.value,void 0===this._deviceId&&(0,p.r)(this,"value-changed",{value:Object.assign(Object.assign({},t.defaultConfig),{},{trigger:"device"})})}},{key:"_deviceTriggerPicked",value:function(e){e.stopPropagation();var t=e.detail.value;this._origTrigger&&(0,y.Po)(this._entityReg,this._origTrigger,t)&&(t=this._origTrigger),this.trigger.id&&(t.id=this.trigger.id),(0,p.r)(this,"value-changed",{value:t})}},{key:"_extraFieldsChanged",value:function(e){e.stopPropagation(),(0,p.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),e.detail.value)})}}],[{key:"defaultConfig",get:function(){return{trigger:"device",device_id:"",domain:"",entity_id:""}}}]);var i}(u.WF);w.styles=(0,u.AH)(k||(k=C`
    ha-device-picker {
      display: block;
      margin-bottom: 24px;
    }

    ha-form {
      display: block;
      margin-top: 24px;
    }
  `)),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,d.__decorate)([(0,h.MZ)({type:Object})],w.prototype,"trigger",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean})],w.prototype,"disabled",void 0),(0,d.__decorate)([(0,h.wk)()],w.prototype,"_deviceId",void 0),(0,d.__decorate)([(0,h.wk)()],w.prototype,"_capabilities",void 0),(0,d.__decorate)([(0,h.wk)(),(0,c.Fg)({context:m.ih,subscribe:!0})],w.prototype,"_entityReg",void 0),w=(0,d.__decorate)([(0,h.EM)("ha-automation-trigger-device")],w),t()}catch(M){t(M)}}))},72503:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),r=i(56038),o=i(69683),n=i(6454),s=(i(28706),i(62826)),l=i(96196),d=i(77845),c=i(92542),u=(i(78740),i(23362)),h=i(31652),g=i(46457),p=e([u,h,g]);[u,h,g]=p.then?(await p)():p;var v,_,f=e=>e,m=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,r=new Array(i),n=0;n<i;n++)r[n]=arguments[n];return(e=(0,o.A)(this,t,[].concat(r))).disabled=!1,e}return(0,n.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e=this.trigger,t=e.event_type,i=e.event_data,a=e.context;return(0,l.qy)(v||(v=f`
      <ha-textfield
        .label=${0}
        name="event_type"
        .value=${0}
        .disabled=${0}
        @change=${0}
      ></ha-textfield>
      <ha-yaml-editor
        .hass=${0}
        .label=${0}
        .name=${0}
        .readOnly=${0}
        .defaultValue=${0}
        @value-changed=${0}
      ></ha-yaml-editor>
      <br />
      ${0}
      <ha-users-picker
        .hass=${0}
        .disabled=${0}
        .value=${0}
        @value-changed=${0}
      ></ha-users-picker>
    `),this.hass.localize("ui.panel.config.automation.editor.triggers.type.event.event_type"),t,this.disabled,this._valueChanged,this.hass,this.hass.localize("ui.panel.config.automation.editor.triggers.type.event.event_data"),"event_data",this.disabled,i,this._dataChanged,this.hass.localize("ui.panel.config.automation.editor.triggers.type.event.context_users"),this.hass,this.disabled,this._wrapUsersInArray(null==a?void 0:a.user_id),this._usersChanged)}},{key:"_wrapUsersInArray",value:function(e){return e?"string"==typeof e?[e]:e:[]}},{key:"_valueChanged",value:function(e){e.stopPropagation(),(0,g.P)(this,e)}},{key:"_dataChanged",value:function(e){e.stopPropagation(),e.detail.isValid&&(0,g.P)(this,e)}},{key:"_usersChanged",value:function(e){e.stopPropagation();var t=Object.assign({},this.trigger);!e.detail.value.length&&t.context?delete t.context.user_id:(t.context||(t.context={}),t.context.user_id=e.detail.value),(0,c.r)(this,"value-changed",{value:t})}}],[{key:"defaultConfig",get:function(){return{trigger:"event",event_type:""}}}])}(l.WF);m.styles=(0,l.AH)(_||(_=f`
    ha-textfield {
      display: block;
    }
  `)),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],m.prototype,"hass",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],m.prototype,"trigger",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean})],m.prototype,"disabled",void 0),m=(0,s.__decorate)([(0,d.EM)("ha-automation-trigger-event")],m),t()}catch(y){t(y)}}))},21738:function(e,t,i){var a,r=i(44734),o=i(56038),n=i(69683),s=i(6454),l=(i(28706),i(62826)),d=(i(91120),i(96196)),c=i(77845),u=i(22786),h=i(92542),g=e=>e,p=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,n.A)(this,t,[].concat(a))).disabled=!1,e._schema=(0,u.A)((e=>[{name:"source",selector:{text:{}}},{name:"zone",selector:{entity:{domain:"zone"}}},{name:"event",type:"select",required:!0,options:[["enter",e("ui.panel.config.automation.editor.triggers.type.geo_location.enter")],["leave",e("ui.panel.config.automation.editor.triggers.type.geo_location.leave")]]}])),e._computeLabelCallback=t=>e.hass.localize(`ui.panel.config.automation.editor.triggers.type.geo_location.${t.name}`),e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){return(0,d.qy)(a||(a=g`
      <ha-form
        .schema=${0}
        .data=${0}
        .hass=${0}
        .disabled=${0}
        .computeLabel=${0}
        @value-changed=${0}
      ></ha-form>
    `),this._schema(this.hass.localize),this.trigger,this.hass,this.disabled,this._computeLabelCallback,this._valueChanged)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,h.r)(this,"value-changed",{value:t})}}],[{key:"defaultConfig",get:function(){return{trigger:"geo_location",source:"",zone:"",event:"enter"}}}])}(d.WF);(0,l.__decorate)([(0,c.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,l.__decorate)([(0,c.MZ)({attribute:!1})],p.prototype,"trigger",void 0),(0,l.__decorate)([(0,c.MZ)({type:Boolean})],p.prototype,"disabled",void 0),p=(0,l.__decorate)([(0,c.EM)("ha-automation-trigger-geo_location")],p)},14822:function(e,t,i){var a,r,o=i(44734),n=i(56038),s=i(69683),l=i(6454),d=(i(28706),i(62826)),c=(i(91120),i(96196)),u=i(77845),h=i(22786),g=i(92542),p=e=>e,v=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(a))).disabled=!1,e._schema=(0,h.A)((e=>[{name:"event",type:"select",required:!0,options:[["start",e("ui.panel.config.automation.editor.triggers.type.homeassistant.start")],["shutdown",e("ui.panel.config.automation.editor.triggers.type.homeassistant.shutdown")]]}])),e._computeLabelCallback=t=>e.hass.localize(`ui.panel.config.automation.editor.triggers.type.homeassistant.${t.name}`),e}return(0,l.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){return(0,c.qy)(a||(a=p`
      <ha-form
        .schema=${0}
        .data=${0}
        .hass=${0}
        .disabled=${0}
        .computeLabel=${0}
        @value-changed=${0}
      ></ha-form>
    `),this._schema(this.hass.localize),this.trigger,this.hass,this.disabled,this._computeLabelCallback,this._valueChanged)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,g.r)(this,"value-changed",{value:t})}}],[{key:"defaultConfig",get:function(){return{trigger:"homeassistant",event:"start"}}}])}(c.WF);v.styles=(0,c.AH)(r||(r=p`
    label {
      display: flex;
      align-items: center;
    }
  `)),(0,d.__decorate)([(0,u.MZ)({attribute:!1})],v.prototype,"hass",void 0),(0,d.__decorate)([(0,u.MZ)({attribute:!1})],v.prototype,"trigger",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],v.prototype,"disabled",void 0),v=(0,d.__decorate)([(0,u.EM)("ha-automation-trigger-homeassistant")],v)},31927:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),r=i(56038),o=i(69683),n=i(6454),s=(i(28706),i(62826)),l=i(96196),d=i(77845),c=i(55376),u=i(82720),h=i(46457),g=e([u,h]);[u,h]=g.then?(await g)():g;var p,v,_=e=>e,f=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,r=new Array(i),n=0;n<i;n++)r[n]=arguments[n];return(e=(0,o.A)(this,t,[].concat(r))).disabled=!1,e}return(0,n.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e=(0,c.e)(this.trigger.triggers);return(0,l.qy)(p||(p=_`
      <ha-automation-trigger
        .triggers=${0}
        .hass=${0}
        .disabled=${0}
        .name=${0}
        @value-changed=${0}
      ></ha-automation-trigger>
    `),e,this.hass,this.disabled,"triggers",this._valueChanged)}},{key:"_valueChanged",value:function(e){(0,h.P)(this,e)}}],[{key:"defaultConfig",get:function(){return{triggers:[]}}}])}(l.WF);f.styles=(0,l.AH)(v||(v=_``)),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],f.prototype,"hass",void 0),(0,s.__decorate)([(0,d.MZ)({attribute:!1})],f.prototype,"trigger",void 0),(0,s.__decorate)([(0,d.MZ)({type:Boolean})],f.prototype,"disabled",void 0),f=(0,s.__decorate)([(0,d.EM)("ha-automation-trigger-list")],f),t()}catch(m){t(m)}}))},14674:function(e,t,i){var a,r=i(94741),o=i(44734),n=i(56038),s=i(69683),l=i(6454),d=(i(16280),i(28706),i(62826)),c=i(96196),u=i(77845),h=i(22786),g=i(68006),p=i(92542),v=i(72125),_=(i(91120),i(55376)),f=e=>e,m=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),n=0;n<i;n++)a[n]=arguments[n];return(e=(0,s.A)(this,t,[].concat(a))).disabled=!1,e._schema=(0,h.A)(((e,t,i,a)=>[{name:"entity_id",required:!0,selector:{entity:{multiple:!0}}},{name:"attribute",selector:{attribute:{entity_id:t?t[0]:void 0,hide_attributes:["access_token","auto_update","available_modes","away_mode","changed_by","code_arm_required","code_format","color_mode","color_modes","current_activity","device_class","editable","effect_list","effect","entity_id","entity_picture","event_type","event_types","fan_mode","fan_modes","fan_speed_list","forecast","friendly_name","frontend_stream_type","has_date","has_time","hs_color","hvac_mode","hvac_modes","icon","id","latest_version","max_color_temp_kelvin","max_mireds","max_temp","media_album_name","media_artist","media_content_type","media_position_updated_at","media_title","min_color_temp_kelvin","min_mireds","min_temp","mode","next_dawn","next_dusk","next_midnight","next_noon","next_rising","next_setting","operation_list","operation_mode","options","percentage_step","precipitation_unit","preset_mode","preset_modes","pressure_unit","release_notes","release_summary","release_url","restored","rgb_color","rgbw_color","shuffle","skipped_version","sound_mode_list","sound_mode","source_list","source_type","source","state_class","step","supported_color_modes","supported_features","swing_mode","swing_modes","target_temp_step","temperature_unit","title","token","unit_of_measurement","user_id","uuid","visibility_unit","wind_speed_unit","xy_color"]}}},{name:"lower_limit",type:"select",required:!0,options:[["value",e("ui.panel.config.automation.editor.triggers.type.numeric_state.type_value")],["input",e("ui.panel.config.automation.editor.triggers.type.numeric_state.type_input")]]}].concat((0,r.A)(i?[{name:"above",selector:{entity:{domain:["input_number","number","sensor"]}}}]:[{name:"above",selector:{number:{mode:"box",min:Number.MIN_SAFE_INTEGER,max:Number.MAX_SAFE_INTEGER,step:.1}}}]),[{name:"upper_limit",type:"select",required:!0,options:[["value",e("ui.panel.config.automation.editor.triggers.type.numeric_state.type_value")],["input",e("ui.panel.config.automation.editor.triggers.type.numeric_state.type_input")]]}],(0,r.A)(a?[{name:"below",selector:{entity:{domain:["input_number","number","sensor"]}}}]:[{name:"below",selector:{number:{mode:"box",min:Number.MIN_SAFE_INTEGER,max:Number.MAX_SAFE_INTEGER,step:.1}}}]),[{name:"value_template",selector:{template:{}}},{name:"for",selector:{duration:{}}}]))),e._data=(0,h.A)(((e,t,i)=>Object.assign(Object.assign({lower_limit:e?"input":"value",upper_limit:t?"input":"value"},i),{},{entity_id:(0,_.e)(i.entity_id),for:(0,g.z)(i.for)}))),e._computeLabelCallback=t=>{switch(t.name){case"entity_id":return e.hass.localize("ui.components.entity.entity-picker.entity");case"attribute":return e.hass.localize("ui.components.entity.entity-attribute-picker.attribute");case"for":return e.hass.localize("ui.panel.config.automation.editor.triggers.type.state.for");default:return e.hass.localize(`ui.panel.config.automation.editor.triggers.type.numeric_state.${t.name}`)}},e}return(0,l.A)(t,e),(0,n.A)(t,[{key:"willUpdate",value:function(e){var t,i;this._inputAboveIsEntity=null!==(t=this._inputAboveIsEntity)&&void 0!==t?t:"string"==typeof this.trigger.above&&(this.trigger.above.startsWith("input_number.")||this.trigger.above.startsWith("number.")||this.trigger.above.startsWith("sensor.")),this._inputBelowIsEntity=null!==(i=this._inputBelowIsEntity)&&void 0!==i?i:"string"==typeof this.trigger.below&&(this.trigger.below.startsWith("input_number.")||this.trigger.below.startsWith("number.")||this.trigger.below.startsWith("sensor.")),e.has("trigger")&&this.trigger&&(0,v.r)(this.trigger.for)&&(0,p.r)(this,"ui-mode-not-available",Error(this.hass.localize("ui.errors.config.no_template_editor_support")))}},{key:"render",value:function(){var e=this._schema(this.hass.localize,this.trigger.entity_id,this._inputAboveIsEntity,this._inputBelowIsEntity),t=this._data(this._inputAboveIsEntity,this._inputBelowIsEntity,this.trigger);return(0,c.qy)(a||(a=f`
      <ha-form
        .hass=${0}
        .data=${0}
        .schema=${0}
        .disabled=${0}
        @value-changed=${0}
        .computeLabel=${0}
      ></ha-form>
    `),this.hass,t,e,this.disabled,this._valueChanged,this._computeLabelCallback)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=Object.assign({},e.detail.value);this._inputAboveIsEntity="input"===t.lower_limit,this._inputBelowIsEntity="input"===t.upper_limit,delete t.lower_limit,delete t.upper_limit,""===t.value_template&&delete t.value_template,(0,p.r)(this,"value-changed",{value:t})}}],[{key:"defaultConfig",get:function(){return{trigger:"numeric_state",entity_id:[]}}}])}(c.WF);(0,d.__decorate)([(0,u.MZ)({attribute:!1})],m.prototype,"hass",void 0),(0,d.__decorate)([(0,u.MZ)({attribute:!1})],m.prototype,"trigger",void 0),(0,d.__decorate)([(0,u.MZ)({type:Boolean})],m.prototype,"disabled",void 0),(0,d.__decorate)([(0,u.wk)()],m.prototype,"_inputAboveIsEntity",void 0),(0,d.__decorate)([(0,u.wk)()],m.prototype,"_inputBelowIsEntity",void 0),m=(0,d.__decorate)([(0,u.EM)("ha-automation-trigger-numeric_state")],m)},55838:function(e,t,i){var a,r,o=i(44734),n=i(56038),s=i(69683),l=i(6454),d=(i(28706),i(62826)),c=i(22786),u=i(96196),h=i(77845),g=i(92542),p=(i(16857),i(90832),i(60733),i(78740),i(91120),e=>e),v=["added","removed"],_=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(a))).disabled=!1,e._schema=(0,c.A)((e=>[{name:"notification_id",required:!1,selector:{text:{}}},{name:"update_type",type:"multi_select",required:!1,options:[["added",e("ui.panel.config.automation.editor.triggers.type.persistent_notification.update_types.added")],["removed",e("ui.panel.config.automation.editor.triggers.type.persistent_notification.update_types.removed")],["current",e("ui.panel.config.automation.editor.triggers.type.persistent_notification.update_types.current")],["updated",e("ui.panel.config.automation.editor.triggers.type.persistent_notification.update_types.updated")]]}])),e._computeLabelCallback=t=>e.hass.localize(`ui.panel.config.automation.editor.triggers.type.persistent_notification.${t.name}`),e}return(0,l.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){var e=this._schema(this.hass.localize);return(0,u.qy)(a||(a=p`
      <ha-form
        .schema=${0}
        .data=${0}
        .hass=${0}
        .disabled=${0}
        .computeLabel=${0}
        @value-changed=${0}
      ></ha-form>
    `),e,this.trigger,this.hass,this.disabled,this._computeLabelCallback,this._valueChanged)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,g.r)(this,"value-changed",{value:t})}}],[{key:"defaultConfig",get:function(){return{trigger:"persistent_notification",update_type:[].concat(v),notification_id:""}}}])}(u.WF);_.styles=(0,u.AH)(r||(r=p`
    ha-textfield {
      display: block;
    }
  `)),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],_.prototype,"trigger",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean})],_.prototype,"disabled",void 0),_=(0,d.__decorate)([(0,h.EM)("ha-automation-trigger-persistent_notification")],_)},96608:function(e,t,i){var a,r,o,n,s,l,d,c,u,h,g=i(61397),p=i(50264),v=i(78261),_=i(44734),f=i(56038),m=i(69683),y=i(6454),b=i(25460),A=(i(52675),i(89463),i(28706),i(50113),i(74423),i(23792),i(62062),i(18111),i(20116),i(7588),i(61701),i(13579),i(5506),i(26099),i(16034),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(23500),i(62953),i(62826)),$=i(96196),k=i(77845),C=i(22786),w=i(92542),M=i(41144),x=(i(70524),i(87156),i(2809),i(84125)),H=i(98995),V=i(62001),L=e=>e,z=e=>e.selector&&!e.required&&!("boolean"in e.selector&&e.default),Z=["trigger","target","alias","id","variables","enabled","options"],O=function(e){function t(){var e;(0,_.A)(this,t);for(var i=arguments.length,n=new Array(i),s=0;s<i;s++)n[s]=arguments[s];return(e=(0,m.A)(this,t,[].concat(n))).disabled=!1,e._checkedKeys=new Set,e._targetSelector=(0,C.A)((e=>e?{target:Object.assign({},e)}:{target:{}})),e._renderField=(t,i,n,s,l)=>{var d,c,u,h,g=null!==(d=null==i?void 0:i.selector)&&void 0!==d?d:{text:null},p=z(i);return i.selector?(0,$.qy)(a||(a=L`<ha-settings-row narrow>
          ${0}
          <span slot="heading"
            >${0}</span
          >
          <span slot="description"
            >${0}</span
          >
          <ha-selector
            .disabled=${0}
            .hass=${0}
            .selector=${0}
            .context=${0}
            .key=${0}
            @value-changed=${0}
            .value=${0}
            .placeholder=${0}
            .localizeValue=${0}
          ></ha-selector>
        </ha-settings-row>`),p?(0,$.qy)(o||(o=L`<ha-checkbox
                .key=${0}
                .checked=${0}
                .disabled=${0}
                @change=${0}
                slot="prefix"
              ></ha-checkbox>`),t,e._checkedKeys.has(t)||(null===(c=e.trigger)||void 0===c?void 0:c.options)&&void 0!==e.trigger.options[t],e.disabled,e._checkboxChanged):n?(0,$.qy)(r||(r=L`<div slot="prefix" class="checkbox-spacer"></div>`)):$.s6,e.hass.localize(`component.${s}.triggers.${l}.fields.${t}.name`)||l,e.hass.localize(`component.${s}.triggers.${l}.fields.${t}.description`),e.disabled||p&&!e._checkedKeys.has(t)&&(!(null!==(u=e.trigger)&&void 0!==u&&u.options)||void 0===e.trigger.options[t]),e.hass,g,e._generateContext(i),t,e._dataChanged,null!==(h=e.trigger)&&void 0!==h&&h.options?e.trigger.options[t]:void 0,i.default,e._localizeValueCallback):$.s6},e._localizeValueCallback=t=>{var i;return null!==(i=e.trigger)&&void 0!==i&&i.trigger?e.hass.localize(`component.${(0,M.m)(e.trigger.trigger)}.selector.${t}`):""},e}return(0,y.A)(t,e),(0,f.A)(t,[{key:"willUpdate",value:function(e){var i,a,r;if((0,b.A)(t,"willUpdate",this,3)([e]),this.hasUpdated||(this.hass.loadBackendTranslation("triggers"),this.hass.loadBackendTranslation("selector")),e.has("trigger")){var o;for(var n in this.trigger)Z.includes(n)||(void 0===o?o=Object.assign(Object.assign({},this.trigger),{},{options:{[n]:this.trigger[n]}}):o.options[n]=this.trigger[n],delete o[n]);void 0!==o&&((0,w.r)(this,"value-changed",{value:o}),this.trigger=o);var s=e.get("trigger");if(null!==(i=this.trigger)&&void 0!==i&&i.trigger){var l=(0,H.zz)(this.trigger.trigger);l!==(0,H.zz)((null==s?void 0:s.trigger)||"")&&this._fetchManifest(l)}else this._manifest=void 0;if((null==s?void 0:s.trigger)!==(null===(a=this.trigger)||void 0===a?void 0:a.trigger)&&this.trigger&&null!==(r=this.description)&&void 0!==r&&r.fields){var d=!1,c={},u=!("options"in this.trigger);Object.entries(this.description.fields).forEach((e=>{var t=(0,v.A)(e,2),i=t[0],a=t[1];a.selector&&a.required&&void 0===a.default&&"boolean"in a.selector&&void 0===c[i]?(d=!0,c[i]=!1):u&&a.selector&&void 0!==a.default&&void 0===c[i]&&(d=!0,c[i]=a.default)})),d&&(0,w.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{options:c})})}}}},{key:"render",value:function(){var e,t,i=(0,H.zz)(this.trigger.trigger),a=(0,H.hN)(this.trigger.trigger),r=this.hass.localize(`component.${i}.triggers.${a}.description`),o=this.description,h=!(null!=o&&o.fields),g=Boolean((null==o?void 0:o.fields)&&Object.values(o.fields).some((e=>z(e))));return(0,$.qy)(n||(n=L`
      <div class="description">
        ${0}
        ${0}
      </div>
      ${0}
      ${0}
    `),r?(0,$.qy)(s||(s=L`<p>${0}</p>`),r):$.s6,this._manifest?(0,$.qy)(l||(l=L`<a
              href=${0}
              title=${0}
              target="_blank"
              rel="noreferrer"
            >
              <ha-icon-button
                .path=${0}
                class="help-icon"
              ></ha-icon-button>
            </a>`),this._manifest.is_built_in?(0,V.o)(this.hass,`/integrations/${this._manifest.domain}`):this._manifest.documentation,this.hass.localize("ui.components.service-control.integration_doc"),"M15.07,11.25L14.17,12.17C13.45,12.89 13,13.5 13,15H11V14.5C11,13.39 11.45,12.39 12.17,11.67L13.41,10.41C13.78,10.05 14,9.55 14,9C14,7.89 13.1,7 12,7A2,2 0 0,0 10,9H8A4,4 0 0,1 12,5A4,4 0 0,1 16,9C16,9.88 15.64,10.67 15.07,11.25M13,19H11V17H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12C22,6.47 17.5,2 12,2Z"):$.s6,o&&"target"in o?(0,$.qy)(d||(d=L`<ha-settings-row narrow>
            ${0}
            <span slot="heading"
              >${0}</span
            >
            <span slot="description"
              >${0}</span
            ><ha-selector
              .hass=${0}
              .selector=${0}
              .disabled=${0}
              @value-changed=${0}
              .value=${0}
            ></ha-selector
          ></ha-settings-row>`),g?(0,$.qy)(c||(c=L`<div slot="prefix" class="checkbox-spacer"></div>`)):$.s6,this.hass.localize("ui.components.service-control.target"),this.hass.localize("ui.components.service-control.target_secondary"),this.hass,this._targetSelector(o.target),this.disabled,this._targetChanged,null===(e=this.trigger)||void 0===e?void 0:e.target):$.s6,h?(0,$.qy)(u||(u=L`<ha-yaml-editor
            .hass=${0}
            .label=${0}
            .name=${0}
            .readOnly=${0}
            .defaultValue=${0}
            @value-changed=${0}
          ></ha-yaml-editor>`),this.hass,this.hass.localize("ui.components.service-control.action_data"),"data",this.disabled,null===(t=this.trigger)||void 0===t?void 0:t.options,this._dataChanged):Object.entries(o.fields).map((e=>{var t=(0,v.A)(e,2),r=t[0],o=t[1];return this._renderField(r,o,g,i,a)})))}},{key:"_generateContext",value:function(e){if(e.context){for(var t={},i=0,a=Object.entries(e.context);i<a.length;i++){var r,o=(0,v.A)(a[i],2),n=o[0],s=o[1];t[n]="target"===s?this.trigger.target:null===(r=this.trigger.options)||void 0===r?void 0:r[s]}return t}}},{key:"_dataChanged",value:function(e){var t,i,a;if(e.stopPropagation(),!1!==e.detail.isValid){var r=e.currentTarget.key,o=e.detail.value;if((null===(t=this.trigger)||void 0===t||null===(t=t.options)||void 0===t?void 0:t[r])!==o&&(null!==(i=this.trigger)&&void 0!==i&&i.options&&r in this.trigger.options||""!==o&&void 0!==o)){var n=Object.assign(Object.assign({},null===(a=this.trigger)||void 0===a?void 0:a.options),{},{[r]:o});(""===o||void 0===o||"object"==typeof o&&!Object.keys(o).length)&&delete n[r],(0,w.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{options:n})})}}}},{key:"_targetChanged",value:function(e){e.stopPropagation(),(0,w.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{target:e.detail.value})})}},{key:"_checkboxChanged",value:function(e){var t,i=e.currentTarget.checked,a=e.currentTarget.key;if(i){var r;this._checkedKeys.add(a);var o,n,s=this.description&&(null===(r=Object.entries(this.description).find((e=>{var t=(0,v.A)(e,2),i=t[0];t[1];return i===a})))||void 0===r?void 0:r[1]),l=null==s?void 0:s.default;if(null==l&&null!=s&&s.selector&&"constant"in s.selector)l=null===(o=s.selector.constant)||void 0===o?void 0:o.value;if(null==l&&null!=s&&s.selector&&"boolean"in s.selector&&(l=!1),null!=l)t=Object.assign(Object.assign({},null===(n=this.trigger)||void 0===n?void 0:n.options),{},{[a]:l})}else{var d;this._checkedKeys.delete(a),delete(t=Object.assign({},null===(d=this.trigger)||void 0===d?void 0:d.options))[a]}t&&(0,w.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{options:t})}),this.requestUpdate("_checkedKeys")}},{key:"_fetchManifest",value:(i=(0,p.A)((0,g.A)().m((function e(t){return(0,g.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return this._manifest=void 0,e.p=1,e.n=2,(0,x.QC)(this.hass,t);case 2:this._manifest=e.v,e.n=4;break;case 3:e.p=3,e.v,console.log(`Unable to fetch integration manifest for ${t}`);case 4:return e.a(2)}}),e,this,[[1,3]])}))),function(e){return i.apply(this,arguments)})}],[{key:"defaultConfig",get:function(){return{trigger:""}}}]);var i}($.WF);O.styles=(0,$.AH)(h||(h=L`
    :host {
      display: block;
      margin: 0px calc(-1 * var(--ha-space-4));
    }
    ha-settings-row {
      padding: 0 var(--ha-space-4);
    }
    ha-settings-row[narrow] {
      padding-bottom: var(--ha-space-2);
    }
    ha-settings-row {
      --settings-row-content-width: 100%;
      --settings-row-prefix-display: contents;
      border-top: var(
        --service-control-items-border-top,
        1px solid var(--divider-color)
      );
    }
    ha-service-picker,
    ha-entity-picker,
    ha-yaml-editor {
      display: block;
      margin: 0 var(--ha-space-4);
    }
    ha-yaml-editor {
      padding: var(--ha-space-4) 0;
    }
    p {
      margin: 0 var(--ha-space-4);
      padding: var(--ha-space-4) 0;
    }
    :host([hide-picker]) p {
      padding-top: 0;
    }
    .checkbox-spacer {
      width: 32px;
    }
    ha-checkbox {
      margin-left: calc(var(--ha-space-4) * -1);
      margin-inline-start: calc(var(--ha-space-4) * -1);
      margin-inline-end: initial;
    }
    .help-icon {
      color: var(--secondary-text-color);
    }
    .description {
      justify-content: space-between;
      display: flex;
      align-items: center;
      padding-right: 2px;
      padding-inline-end: 2px;
      padding-inline-start: initial;
    }
    .description p {
      direction: ltr;
    }
  `)),(0,A.__decorate)([(0,k.MZ)({attribute:!1})],O.prototype,"hass",void 0),(0,A.__decorate)([(0,k.MZ)({attribute:!1})],O.prototype,"trigger",void 0),(0,A.__decorate)([(0,k.MZ)({attribute:!1})],O.prototype,"description",void 0),(0,A.__decorate)([(0,k.MZ)({type:Boolean})],O.prototype,"disabled",void 0),(0,A.__decorate)([(0,k.wk)()],O.prototype,"_checkedKeys",void 0),(0,A.__decorate)([(0,k.wk)()],O.prototype,"_manifest",void 0),O=(0,A.__decorate)([(0,k.EM)("ha-automation-trigger-platform")],O)},24590:function(e,t,i){var a,r=i(44734),o=i(56038),n=i(69683),s=i(6454),l=(i(16280),i(28706),i(74423),i(18111),i(7588),i(26099),i(23500),i(62826)),d=i(96196),c=i(77845),u=i(96685),h=i(22786),g=i(55376),p=i(92542),v=i(72125),_=i(47916),f=i(20897),m=(i(91120),i(68006)),y=e=>e,b=(0,u.kp)(f.V,(0,u.Ik)({alias:(0,u.lq)((0,u.Yj)()),trigger:(0,u.eu)("state"),entity_id:(0,u.lq)((0,u.KC)([(0,u.Yj)(),(0,u.YO)((0,u.Yj)())])),attribute:(0,u.lq)((0,u.Yj)()),from:(0,u.lq)((0,u.KC)([(0,u.me)((0,u.Yj)()),(0,u.YO)((0,u.Yj)())])),to:(0,u.lq)((0,u.KC)([(0,u.me)((0,u.Yj)()),(0,u.YO)((0,u.Yj)())])),for:(0,u.lq)((0,u.KC)([(0,u.ai)(),(0,u.Yj)(),f.b]))})),A=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,n.A)(this,t,[].concat(a))).disabled=!1,e._schema=(0,h.A)(((e,t,i,a)=>[{name:"entity_id",required:!0,selector:{entity:{multiple:!0}}},{name:"attribute",context:{filter_entity:"entity_id"},selector:{attribute:{hide_attributes:["access_token","available_modes","code_arm_required","code_format","color_modes","device_class","editable","effect_list","entity_id","entity_picture","event_types","fan_modes","fan_speed_list","friendly_name","frontend_stream_type","has_date","has_time","hvac_modes","icon","id","max_color_temp_kelvin","max_mireds","max_temp","max","min_color_temp_kelvin","min_mireds","min_temp","min","mode","operation_list","options","percentage_step","precipitation_unit","preset_modes","pressure_unit","sound_mode_list","source_list","state_class","step","supported_color_modes","supported_features","swing_modes","target_temp_step","temperature_unit","token","unit_of_measurement","visibility_unit","wind_speed_unit"]}}},{name:"from",context:{filter_entity:"entity_id"},selector:{state:{multiple:!0,extra_options:t?[]:[{label:e("ui.panel.config.automation.editor.triggers.type.state.any_state_ignore_attributes"),value:_.x}],attribute:t,hide_states:i}}},{name:"to",context:{filter_entity:"entity_id"},selector:{state:{multiple:!0,extra_options:t?[]:[{label:e("ui.panel.config.automation.editor.triggers.type.state.any_state_ignore_attributes"),value:_.x}],attribute:t,hide_states:a}}},{name:"for",selector:{duration:{}}}])),e._computeLabelCallback=t=>e.hass.localize("entity_id"===t.name?"ui.components.entity.entity-picker.entity":`ui.panel.config.automation.editor.triggers.type.state.${t.name}`),e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"shouldUpdate",value:function(e){if(!e.has("trigger"))return!0;if(this.trigger.for&&"object"==typeof this.trigger.for&&0===this.trigger.for.milliseconds&&delete this.trigger.for.milliseconds,this.trigger&&(0,v.r)(this.trigger))return(0,p.r)(this,"ui-mode-not-available",Error(this.hass.localize("ui.errors.config.no_template_editor_support"))),!1;try{(0,u.vA)(this.trigger,b)}catch(t){return(0,p.r)(this,"ui-mode-not-available",t),!1}return!0}},{key:"render",value:function(){var e=(0,m.z)(this.trigger.for),t=Object.assign(Object.assign({},this.trigger),{},{entity_id:(0,g.e)(this.trigger.entity_id),for:e});t.to=this._normalizeStates(this.trigger.to,t.attribute),t.from=this._normalizeStates(this.trigger.from,t.attribute);var i=this._schema(this.hass.localize,this.trigger.attribute,t.to,t.from);return(0,d.qy)(a||(a=y`
      <ha-form
        .hass=${0}
        .data=${0}
        .schema=${0}
        @value-changed=${0}
        .computeLabel=${0}
        .disabled=${0}
      ></ha-form>
    `),this.hass,t,i,this._valueChanged,this._computeLabelCallback,this.disabled)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value;t.to=this._applyAnyStateExclusive(t.to,t.attribute),Array.isArray(t.to)&&0===t.to.length&&delete t.to,t.from=this._applyAnyStateExclusive(t.from,t.attribute),Array.isArray(t.from)&&0===t.from.length&&delete t.from,Object.keys(t).forEach((e=>{var i=t[e];void 0!==i&&""!==i||delete t[e]})),(0,p.r)(this,"value-changed",{value:t})}},{key:"_applyAnyStateExclusive",value:function(e,t){return(Array.isArray(e)?e.includes(_.x):e===_.x)?t?void 0:null:e}},{key:"_normalizeStates",value:function(e,t){return t||null!==e?null==e?[]:(0,g.e)(e):[_.x]}}],[{key:"defaultConfig",get:function(){return{trigger:"state",entity_id:[]}}}])}(d.WF);(0,l.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"hass",void 0),(0,l.__decorate)([(0,c.MZ)({attribute:!1})],A.prototype,"trigger",void 0),(0,l.__decorate)([(0,c.MZ)({type:Boolean})],A.prototype,"disabled",void 0),A=(0,l.__decorate)([(0,c.EM)("ha-automation-trigger-state")],A)},77461:function(e,t,i){var a,r=i(44734),o=i(56038),n=i(69683),s=i(6454),l=(i(28706),i(62826)),d=i(96196),c=i(77845),u=i(22786),h=i(92542),g=(i(91120),e=>e),p=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,n.A)(this,t,[].concat(a))).disabled=!1,e._schema=(0,u.A)((e=>[{name:"event",type:"select",required:!0,options:[["sunrise",e("ui.panel.config.automation.editor.triggers.type.sun.sunrise")],["sunset",e("ui.panel.config.automation.editor.triggers.type.sun.sunset")]]},{name:"offset",selector:{text:{}}}])),e._computeLabelCallback=t=>e.hass.localize(`ui.panel.config.automation.editor.triggers.type.sun.${t.name}`),e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){var e=this._schema(this.hass.localize);return(0,d.qy)(a||(a=g`
      <ha-form
        .schema=${0}
        .data=${0}
        .hass=${0}
        .disabled=${0}
        .computeLabel=${0}
        @value-changed=${0}
      ></ha-form>
    `),e,this.trigger,this.hass,this.disabled,this._computeLabelCallback,this._valueChanged)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,h.r)(this,"value-changed",{value:t})}}],[{key:"defaultConfig",get:function(){return{trigger:"sun",event:"sunrise",offset:0}}}])}(d.WF);(0,l.__decorate)([(0,c.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,l.__decorate)([(0,c.MZ)({attribute:!1})],p.prototype,"trigger",void 0),(0,l.__decorate)([(0,c.MZ)({type:Boolean})],p.prototype,"disabled",void 0),p=(0,l.__decorate)([(0,c.EM)("ha-automation-trigger-sun")],p)},93479:function(e,t,i){var a,r,o,n=i(61397),s=i(50264),l=i(44734),d=i(56038),c=i(69683),u=i(6454),h=i(25460),g=(i(28706),i(62062),i(26910),i(18111),i(61701),i(26099),i(62826)),p=i(96196),v=i(77845),_=i(92542),f=i(25749),m=(i(69869),i(56565),function(){var e=(0,s.A)((0,n.A)().m((function e(t){return(0,n.A)().w((function(e){for(;;)if(0===e.n)return e.a(2,t.callWS({type:"tag/list"}))}),e)})));return function(t){return e.apply(this,arguments)}}()),y=e=>e,b=function(e){function t(){var e;(0,l.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,c.A)(this,t,[].concat(a))).disabled=!1,e}return(0,u.A)(t,e),(0,d.A)(t,[{key:"firstUpdated",value:function(e){(0,h.A)(t,"firstUpdated",this,3)([e]),this._fetchTags()}},{key:"render",value:function(){return this._tags?(0,p.qy)(a||(a=y`
      <ha-select
        .label=${0}
        .disabled=${0}
        .value=${0}
        @selected=${0}
        fixedMenuPosition
        naturalMenuWidth
      >
        ${0}
      </ha-select>
    `),this.hass.localize("ui.panel.config.automation.editor.triggers.type.tag.label"),this.disabled||0===this._tags.length,this.trigger.tag_id,this._tagChanged,this._tags.map((e=>(0,p.qy)(r||(r=y`
            <ha-list-item .value=${0}>
              ${0}
            </ha-list-item>
          `),e.id,e.name||e.id)))):p.s6}},{key:"_fetchTags",value:(i=(0,s.A)((0,n.A)().m((function e(){return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,m(this.hass);case 1:this._tags=e.v.sort(((e,t)=>(0,f.SH)(e.name||e.id,t.name||t.id,this.hass.locale.language)));case 2:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_tagChanged",value:function(e){e.target.value&&this._tags&&this.trigger.tag_id!==e.target.value&&(0,_.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{tag_id:e.target.value})})}}],[{key:"defaultConfig",get:function(){return{trigger:"tag",tag_id:""}}}]);var i}(p.WF);b.styles=(0,p.AH)(o||(o=y`
    ha-select {
      display: block;
    }
  `)),(0,g.__decorate)([(0,v.MZ)({attribute:!1})],b.prototype,"hass",void 0),(0,g.__decorate)([(0,v.MZ)({attribute:!1})],b.prototype,"trigger",void 0),(0,g.__decorate)([(0,v.MZ)({type:Boolean})],b.prototype,"disabled",void 0),(0,g.__decorate)([(0,v.wk)()],b.prototype,"_tags",void 0),b=(0,g.__decorate)([(0,v.EM)("ha-automation-trigger-tag")],b)},95669:function(e,t,i){var a,r=i(44734),o=i(56038),n=i(69683),s=i(6454),l=(i(16280),i(28706),i(18111),i(81148),i(26099),i(16034),i(62826)),d=(i(67591),i(96196)),c=i(77845),u=(i(91120),i(68006)),h=i(92542),g=i(72125),p=e=>e,v=[{name:"value_template",required:!0,selector:{template:{}}},{name:"for",selector:{duration:{}}}],_=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,n.A)(this,t,[].concat(a))).disabled=!1,e._computeLabelCallback=t=>e.hass.localize(`ui.panel.config.automation.editor.triggers.type.template.${t.name}`),e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"willUpdate",value:function(e){e.has("trigger")&&this.trigger&&(0,g.r)(this.trigger.for)&&(0,h.r)(this,"ui-mode-not-available",Error(this.hass.localize("ui.errors.config.no_template_editor_support")))}},{key:"render",value:function(){var e=(0,u.z)(this.trigger.for),t=Object.assign(Object.assign({},this.trigger),{},{for:e});return(0,d.qy)(a||(a=p`
      <ha-form
        .hass=${0}
        .data=${0}
        .schema=${0}
        @value-changed=${0}
        .computeLabel=${0}
        .disabled=${0}
      ></ha-form>
    `),this.hass,t,v,this._valueChanged,this._computeLabelCallback,this.disabled)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value;t.for&&Object.values(t.for).every((e=>0===e))&&delete t.for,(0,h.r)(this,"value-changed",{value:t})}}],[{key:"defaultConfig",get:function(){return{trigger:"template",value_template:""}}}])}(d.WF);(0,l.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,l.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"trigger",void 0),(0,l.__decorate)([(0,c.MZ)({type:Boolean})],_.prototype,"disabled",void 0),_=(0,l.__decorate)([(0,c.EM)("ha-automation-trigger-template")],_)},70234:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(94741),r=i(44734),o=i(56038),n=i(69683),s=i(6454),l=(i(16280),i(18107),i(28706),i(74423),i(62062),i(34782),i(18111),i(61701),i(26099),i(67357),i(62826)),d=i(96196),c=i(77845),u=i(22786),h=i(10253),g=i(92542),p=(i(91120),i(41144)),v=e([h]);h=(v.then?(await v)():v)[0];var _,f=e=>e,m="time",y="entity",b=["sensor","input_datetime"],A=["sun","mon","tue","wed","thu","fri","sat"],$=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,o=new Array(i),s=0;s<i;s++)o[s]=arguments[s];return(e=(0,n.A)(this,t,[].concat(o))).disabled=!1,e._schema=(0,u.A)(((e,t,i)=>{var r=(0,h.P)(t),o=A.slice(r,A.length).concat(A.slice(0,r));return[{name:"mode",type:"select",required:!0,options:[[m,e("ui.panel.config.automation.editor.triggers.type.time.type_value")],[y,e("ui.panel.config.automation.editor.triggers.type.time.type_input")]]}].concat((0,a.A)(i===m?[{name:"time",selector:{time:{}}}]:[{name:"entity",selector:{entity:{filter:[{domain:"input_datetime"},{domain:"sensor",device_class:"timestamp"}]}}},{name:"offset",selector:{text:{}}}]),[{type:"multi_select",name:"weekday",options:o.map((t=>[t,e(`ui.panel.config.automation.editor.triggers.type.time.weekdays.${t}`)]))}])})),e._data=(0,u.A)(((e,t,i)=>{var a="object"==typeof t?t.entity_id:t&&b.includes((0,p.m)(t))?t:void 0,r=a?void 0:t,o="object"==typeof t?t.offset:void 0;return{mode:null!=e?e:a?y:m,entity:a,time:r,offset:o,weekday:i}})),e._computeLabelCallback=t=>{switch(t.name){case"time":return e.hass.localize("ui.panel.config.automation.editor.triggers.type.time.at");case"weekday":return e.hass.localize("ui.panel.config.automation.editor.triggers.type.time.weekday")}return e.hass.localize(`ui.panel.config.automation.editor.triggers.type.time.${t.name}`)},e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"willUpdate",value:function(e){e.has("trigger")&&this.trigger&&Array.isArray(this.trigger.at)&&(0,g.r)(this,"ui-mode-not-available",Error(this.hass.localize("ui.errors.config.editor_not_supported")))}},{key:"render",value:function(){var e=this.trigger.at;if(Array.isArray(e))return d.s6;var t=this._data(this._inputMode,e,this.trigger.weekday),i=this._schema(this.hass.localize,this.hass.locale,t.mode);return(0,d.qy)(_||(_=f`
      <ha-form
        .hass=${0}
        .data=${0}
        .schema=${0}
        .disabled=${0}
        @value-changed=${0}
        .computeLabel=${0}
      ></ha-form>
    `),this.hass,t,i,this.disabled,this._valueChanged,this._computeLabelCallback)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=Object.assign({},e.detail.value);this._inputMode=t.mode;var i=t.weekday;delete t.weekday,t.mode===m?(delete t.entity,delete t.offset):delete t.time;var a=Object.assign(Object.assign({},this.trigger),{},{at:t.offset?{entity_id:t.entity,offset:t.offset}:t.entity||t.time});i&&i.length>0?a.weekday=i:delete a.weekday,(0,g.r)(this,"value-changed",{value:a})}}],[{key:"defaultConfig",get:function(){return{trigger:"time",at:""}}}])}(d.WF);(0,l.__decorate)([(0,c.MZ)({attribute:!1})],$.prototype,"hass",void 0),(0,l.__decorate)([(0,c.MZ)({attribute:!1})],$.prototype,"trigger",void 0),(0,l.__decorate)([(0,c.MZ)({type:Boolean})],$.prototype,"disabled",void 0),(0,l.__decorate)([(0,c.wk)()],$.prototype,"_inputMode",void 0),$=(0,l.__decorate)([(0,c.EM)("ha-automation-trigger-time")],$),t()}catch(k){t(k)}}))},35215:function(e,t,i){var a,r=i(44734),o=i(56038),n=i(69683),s=i(6454),l=(i(28706),i(62826)),d=i(96196),c=i(77845),u=i(92542),h=(i(91120),e=>e),g=[{name:"hours",selector:{text:{}}},{name:"minutes",selector:{text:{}}},{name:"seconds",selector:{text:{}}}],p=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,n.A)(this,t,[].concat(a))).disabled=!1,e._computeLabelCallback=t=>e.hass.localize(`ui.panel.config.automation.editor.triggers.type.time_pattern.${t.name}`),e._computeHelperCallback=t=>e.hass.localize("ui.panel.config.automation.editor.triggers.type.time_pattern.help"),e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){return(0,d.qy)(a||(a=h`
      <ha-form
        .hass=${0}
        .schema=${0}
        .data=${0}
        .disabled=${0}
        .computeLabel=${0}
        .computeHelper=${0}
        @value-changed=${0}
      ></ha-form>
    `),this.hass,g,this.trigger,this.disabled,this._computeLabelCallback,this._computeHelperCallback,this._valueChanged)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,u.r)(this,"value-changed",{value:t})}}],[{key:"defaultConfig",get:function(){return{trigger:"time_pattern"}}}])}(d.WF);(0,l.__decorate)([(0,c.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,l.__decorate)([(0,c.MZ)({attribute:!1})],p.prototype,"trigger",void 0),(0,l.__decorate)([(0,c.MZ)({type:Boolean})],p.prototype,"disabled",void 0),p=(0,l.__decorate)([(0,c.EM)("ha-automation-trigger-time_pattern")],p)},35562:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),r=i(50264),o=i(94741),n=i(44734),s=i(56038),l=i(69683),d=i(6454),c=i(25460),u=(i(28706),i(74423),i(25276),i(23792),i(62062),i(44114),i(54554),i(54743),i(11745),i(16573),i(78100),i(77936),i(26099),i(27495),i(25440),i(21489),i(48140),i(75044),i(21903),i(91134),i(28845),i(373),i(41405),i(37467),i(44732),i(33684),i(79577),i(41549),i(49797),i(49631),i(35623),i(55815),i(64979),i(79739),i(62826)),h=i(96196),g=i(77845),p=i(92542),v=i(93777),_=i(4657),f=i(55124),m=(i(16857),i(90832),i(60733),i(78740),i(4848)),y=i(46457),b=e([y]);y=(b.then?(await b)():b)[0];var A,$,k,C=e=>e,w=["GET","HEAD","POST","PUT"],M=["POST","PUT"],x=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,l.A)(this,t,[].concat(a))).disabled=!1,e}return(0,d.A)(t,e),(0,s.A)(t,[{key:"connectedCallback",value:function(){(0,c.A)(t,"connectedCallback",this,3)([]);var e={callback:e=>{this._config=e}};(0,p.r)(this,"subscribe-automation-config",e),this._unsub=e.unsub}},{key:"disconnectedCallback",value:function(){(0,c.A)(t,"disconnectedCallback",this,3)([]),this._unsub&&this._unsub()}},{key:"_generateWebhookId",value:function(){var e,t=crypto.getRandomValues(new Uint8Array(18)),i=btoa(String.fromCharCode.apply(String,(0,o.A)(t))).replace(/\+/g,"-").replace(/\//g,"_");return`${(0,v.Y)((null===(e=this._config)||void 0===e?void 0:e.alias)||"","-")}-${i}`}},{key:"willUpdate",value:function(e){(0,c.A)(t,"willUpdate",this,3)([e]),e.has("trigger")&&(void 0===this.trigger.allowed_methods&&(this.trigger.allowed_methods=[].concat(M)),void 0===this.trigger.local_only&&(this.trigger.local_only=!0),""===this.trigger.webhook_id&&(this.trigger.webhook_id=this._generateWebhookId()))}},{key:"render",value:function(){var e=this.trigger,t=e.allowed_methods,i=e.local_only,a=e.webhook_id;return(0,h.qy)(A||(A=C`
      <div class="flex">
        <ha-textfield
          name="webhook_id"
          .label=${0}
          .helper=${0}
          .disabled=${0}
          iconTrailing
          .value=${0}
          @input=${0}
        >
          <ha-icon-button
            @click=${0}
            slot="trailingIcon"
            .label=${0}
            .path=${0}
          ></ha-icon-button>
        </ha-textfield>
        <ha-button-menu multi @closed=${0} fixed>
          <ha-icon-button
            slot="trigger"
            .label=${0}
            .path=${0}
          ></ha-icon-button>
          ${0}
          <li divider role="separator"></li>
          <ha-check-list-item
            left
            @request-selected=${0}
            .selected=${0}
          >
            ${0}
          </ha-check-list-item>
        </ha-button-menu>
      </div>
    `),this.hass.localize("ui.panel.config.automation.editor.triggers.type.webhook.webhook_id"),this.hass.localize("ui.panel.config.automation.editor.triggers.type.webhook.webhook_id_helper"),this.disabled,a||"",this._valueChanged,this._copyUrl,this.hass.localize("ui.panel.config.automation.editor.triggers.type.webhook.copy_url"),"M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z",f.d,this.hass.localize("ui.panel.config.automation.editor.triggers.type.webhook.webhook_settings"),"M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z",w.map((e=>(0,h.qy)($||($=C`
              <ha-check-list-item
                left
                .value=${0}
                @request-selected=${0}
                .selected=${0}
              >
                ${0}
              </ha-check-list-item>
            `),e,this._allowedMethodsChanged,t.includes(e),e))),this._localOnlyChanged,i,this.hass.localize("ui.panel.config.automation.editor.triggers.type.webhook.local_only"))}},{key:"_valueChanged",value:function(e){(0,y.P)(this,e)}},{key:"_localOnlyChanged",value:function(e){if(e.stopPropagation(),this.trigger.local_only!==e.detail.selected){var t=Object.assign(Object.assign({},this.trigger),{},{local_only:e.detail.selected});(0,p.r)(this,"value-changed",{value:t})}}},{key:"_allowedMethodsChanged",value:function(e){var t,i;e.stopPropagation();var a=e.target.value,r=e.detail.selected;if(r!==(null===(t=this.trigger.allowed_methods)||void 0===t?void 0:t.includes(a))){var n=null!==(i=this.trigger.allowed_methods)&&void 0!==i?i:[],s=(0,o.A)(n);r?s.push(a):s.splice(s.indexOf(a),1);var l=Object.assign(Object.assign({},this.trigger),{},{allowed_methods:s});(0,p.r)(this,"value-changed",{value:l})}}},{key:"_copyUrl",value:(i=(0,r.A)((0,a.A)().m((function e(t){var i,r;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return i=t.target.parentElement,r=this.hass.hassUrl(`/api/webhook/${i.value}`),e.n=1,(0,_.l)(r);case 1:(0,m.P)(this,{message:this.hass.localize("ui.common.copied_clipboard")});case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})}],[{key:"defaultConfig",get:function(){return{trigger:"webhook",allowed_methods:[].concat(M),local_only:!0,webhook_id:""}}}]);var i}(h.WF);x.styles=(0,h.AH)(k||(k=C`
    .flex {
      display: flex;
    }

    ha-textfield {
      flex: 1;
    }

    ha-textfield > ha-icon-button {
      --mdc-icon-button-size: 24px;
      --mdc-icon-size: 18px;
      color: var(--secondary-text-color);
    }

    ha-button-menu {
      padding-top: 4px;
    }
  `)),(0,u.__decorate)([(0,g.MZ)({attribute:!1})],x.prototype,"hass",void 0),(0,u.__decorate)([(0,g.MZ)({attribute:!1})],x.prototype,"trigger",void 0),(0,u.__decorate)([(0,g.MZ)({type:Boolean})],x.prototype,"disabled",void 0),(0,u.__decorate)([(0,g.wk)()],x.prototype,"_config",void 0),x=(0,u.__decorate)([(0,g.EM)("ha-automation-trigger-webhook")],x),t()}catch(H){t(H)}}))},36797:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),r=i(56038),o=i(69683),n=i(6454),s=(i(28706),i(62826)),l=i(82965),d=(i(48543),i(96196)),c=i(77845),u=i(92542),h=i(97382),g=i(28724),p=e([l]);l=(p.then?(await p)():p)[0];var v,_,f=e=>e;function A(e){return(0,g.e)(e)&&"zone"!==(0,h.t)(e)}var m=["zone"],y=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,r=new Array(i),n=0;n<i;n++)r[n]=arguments[n];return(e=(0,o.A)(this,t,[].concat(r))).disabled=!1,e}return(0,n.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e=this.trigger,t=e.entity_id,i=e.zone,a=e.event;return(0,d.qy)(v||(v=f`
      <ha-entity-picker
        .label=${0}
        .value=${0}
        .disabled=${0}
        @value-changed=${0}
        .hass=${0}
        allow-custom-entity
        .entityFilter=${0}
      ></ha-entity-picker>
      <ha-entity-picker
        .label=${0}
        .value=${0}
        .disabled=${0}
        @value-changed=${0}
        .hass=${0}
        allow-custom-entity
        .includeDomains=${0}
      ></ha-entity-picker>

      <label>
        ${0}
        <ha-formfield
          .disabled=${0}
          .label=${0}
        >
          <ha-radio
            name="event"
            value="enter"
            .disabled=${0}
            .checked=${0}
            @change=${0}
          ></ha-radio>
        </ha-formfield>
        <ha-formfield
          .disabled=${0}
          .label=${0}
        >
          <ha-radio
            name="event"
            value="leave"
            .disabled=${0}
            .checked=${0}
            @change=${0}
          ></ha-radio>
        </ha-formfield>
      </label>
    `),this.hass.localize("ui.panel.config.automation.editor.triggers.type.zone.entity"),t,this.disabled,this._entityPicked,this.hass,A,this.hass.localize("ui.panel.config.automation.editor.triggers.type.zone.zone"),i,this.disabled,this._zonePicked,this.hass,m,this.hass.localize("ui.panel.config.automation.editor.triggers.type.zone.event"),this.disabled,this.hass.localize("ui.panel.config.automation.editor.triggers.type.zone.enter"),this.disabled,"enter"===a,this._radioGroupPicked,this.disabled,this.hass.localize("ui.panel.config.automation.editor.triggers.type.zone.leave"),this.disabled,"leave"===a,this._radioGroupPicked)}},{key:"_entityPicked",value:function(e){e.stopPropagation(),(0,u.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{entity_id:e.detail.value})})}},{key:"_zonePicked",value:function(e){e.stopPropagation(),(0,u.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{zone:e.detail.value})})}},{key:"_radioGroupPicked",value:function(e){e.stopPropagation(),(0,u.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.trigger),{},{event:e.target.value})})}}],[{key:"defaultConfig",get:function(){return{trigger:"zone",entity_id:"",zone:"",event:"enter"}}}])}(d.WF);y.styles=(0,d.AH)(_||(_=f`
    label {
      display: flex;
      align-items: center;
    }
    ha-entity-picker {
      display: block;
      margin-bottom: 24px;
    }
  `)),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,s.__decorate)([(0,c.MZ)({attribute:!1})],y.prototype,"trigger",void 0),(0,s.__decorate)([(0,c.MZ)({type:Boolean})],y.prototype,"disabled",void 0),y=(0,s.__decorate)([(0,c.EM)("ha-automation-trigger-zone")],y),t()}catch(b){t(b)}}))},36387:function(e,t,i){i.d(t,{h:function(){return A}});var a=i(61397),r=i(50264),o=i(44734),n=i(56038),s=i(69683),l=i(6454),d=i(62826),c=i(77845),u=i(69162),h=i(47191),g=function(e){function t(){return(0,o.A)(this,t),(0,s.A)(this,t,arguments)}return(0,l.A)(t,e),(0,n.A)(t)}(u.L);g.styles=[h.R],g=(0,d.__decorate)([(0,c.EM)("mwc-checkbox")],g);var p,v,_,f=i(96196),m=i(94333),y=i(27686),b=e=>e,A=function(e){function t(){var e;return(0,o.A)(this,t),(e=(0,s.A)(this,t,arguments)).left=!1,e.graphic="control",e}return(0,l.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){var e={"mdc-deprecated-list-item__graphic":this.left,"mdc-deprecated-list-item__meta":!this.left},t=this.renderText(),i=this.graphic&&"control"!==this.graphic&&!this.left?this.renderGraphic():(0,f.qy)(p||(p=b``)),a=this.hasMeta&&this.left?this.renderMeta():(0,f.qy)(v||(v=b``)),r=this.renderRipple();return(0,f.qy)(_||(_=b`
      ${0}
      ${0}
      ${0}
      <span class=${0}>
        <mwc-checkbox
            reducedTouchTarget
            tabindex=${0}
            .checked=${0}
            ?disabled=${0}
            @change=${0}>
        </mwc-checkbox>
      </span>
      ${0}
      ${0}`),r,i,this.left?"":t,(0,m.H)(e),this.tabindex,this.selected,this.disabled,this.onChange,this.left?t:"",a)}},{key:"onChange",value:(i=(0,r.A)((0,a.A)().m((function e(t){var i;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:if(i=t.target,this.selected===i.checked){e.n=2;break}return this._skipPropRequest=!0,this.selected=i.checked,e.n=1,this.updateComplete;case 1:this._skipPropRequest=!1;case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})}]);var i}(y.J);(0,d.__decorate)([(0,c.P)("slot")],A.prototype,"slotElement",void 0),(0,d.__decorate)([(0,c.P)("mwc-checkbox")],A.prototype,"checkboxElement",void 0),(0,d.__decorate)([(0,c.MZ)({type:Boolean})],A.prototype,"left",void 0),(0,d.__decorate)([(0,c.MZ)({type:String,reflect:!0})],A.prototype,"graphic",void 0)},34875:function(e,t,i){i.d(t,{R:function(){return r}});var a,r=(0,i(96196).AH)(a||(a=(e=>e)`:host(:not([twoline])){height:56px}:host(:not([left])) .mdc-deprecated-list-item__meta{height:40px;width:40px}`))},58673:function(e,t,i){i.d(t,{a:function(){return u}});var a=i(78261),r=i(44734),o=i(56038),n=i(69683),s=i(6454),l=(i(23418),i(18111),i(81148),i(26099),i(4610)),d=i(42017),c={},u=(0,d.u$)(function(e){function t(){var e;return(0,r.A)(this,t),(e=(0,n.A)(this,t,arguments)).ot=c,e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(e,t){return t()}},{key:"update",value:function(e,t){var i=(0,a.A)(t,2),r=i[0],o=i[1];if(Array.isArray(r)){if(Array.isArray(this.ot)&&this.ot.length===r.length&&r.every(((e,t)=>e===this.ot[t])))return l.c0}else if(this.ot===r)return l.c0;return this.ot=Array.isArray(r)?Array.from(r):r,this.render(r,o)}}])}(d.WL))}}]);
//# sourceMappingURL=3538.46aee90c425e48de.js.map