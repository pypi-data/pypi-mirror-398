"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["7298"],{10393:function(e,t,a){a.d(t,{M:function(){return r},l:function(){return i}});a(23792),a(26099),a(31415),a(17642),a(58004),a(33853),a(45876),a(32475),a(15024),a(31698),a(62953);var i=new Set(["primary","accent","disabled","red","pink","purple","deep-purple","indigo","blue","light-blue","cyan","teal","green","light-green","lime","yellow","amber","orange","deep-orange","brown","light-grey","grey","dark-grey","blue-grey","black","white"]);function r(e){return i.has(e)?`var(--${e}-color)`:e}},80990:function(e,t,a){a.a(e,(async function(e,t){try{var i=a(61397),r=a(50264),o=a(94741),n=a(44734),l=a(56038),s=a(69683),c=a(6454),d=(a(28706),a(2008),a(74423),a(23792),a(62062),a(18111),a(22489),a(61701),a(36033),a(26099),a(31415),a(17642),a(58004),a(33853),a(45876),a(32475),a(15024),a(31698),a(62953),a(62826)),u=a(96196),h=a(77845),p=a(22786),v=a(92542),b=a(41327),_=a(10234),y=a(10085),f=a(61940),m=a(96943),g=(a(60961),e([m]));m=(g.then?(await g)():g)[0];var k,A,w,$,M,Z,L=e=>e,V="M17.63,5.84C17.27,5.33 16.67,5 16,5H5A2,2 0 0,0 3,7V17A2,2 0 0,0 5,19H16C16.67,19 17.27,18.66 17.63,18.15L22,12L17.63,5.84Z",x="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",H="___ADD_NEW___",C="___NO_LABELS___",E=function(e){function t(){var e;(0,n.A)(this,t);for(var a=arguments.length,i=new Array(a),r=0;r<a;r++)i[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(i))).noAdd=!1,e.disabled=!1,e.required=!1,e._labelMap=(0,p.A)((e=>e?new Map(e.map((e=>[e.label_id,e]))):new Map)),e._computeValueRenderer=(0,p.A)((t=>a=>{var i=e._labelMap(t).get(a);return i?(0,u.qy)(A||(A=L`
          ${0}
          <span slot="headline">${0}</span>
        `),i.icon?(0,u.qy)(w||(w=L`<ha-icon slot="start" .icon=${0}></ha-icon>`),i.icon):(0,u.qy)($||($=L`<ha-svg-icon slot="start" .path=${0}></ha-svg-icon>`),V),i.name):(0,u.qy)(k||(k=L`
            <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
            <span slot="headline">${0}</span>
          `),V,a)})),e._getLabelsMemoized=(0,p.A)(b.IV),e._getItems=()=>e._labels&&0!==e._labels.length?e._getLabelsMemoized(e.hass.states,e.hass.areas,e.hass.devices,e.hass.entities,e._labels,e.includeDomains,e.excludeDomains,e.includeDeviceClasses,e.deviceFilter,e.entityFilter,e.excludeLabels):[{id:C,primary:e.hass.localize("ui.components.label-picker.no_labels"),icon_path:V}],e._allLabelNames=(0,p.A)((e=>e?(0,o.A)(new Set(e.map((e=>e.name.toLowerCase())).filter(Boolean))):[])),e._getAdditionalItems=t=>{if(e.noAdd)return[];var a=e._allLabelNames(e._labels);return t&&!a.includes(t.toLowerCase())?[{id:H+t,primary:e.hass.localize("ui.components.label-picker.add_new_sugestion",{name:t}),icon_path:x}]:[{id:H,primary:e.hass.localize("ui.components.label-picker.add_new"),icon_path:x}]},e._notFoundLabel=t=>e.hass.localize("ui.components.label-picker.no_match",{term:(0,u.qy)(M||(M=L`<b>‘${0}’</b>`),t)}),e}return(0,c.A)(t,e),(0,l.A)(t,[{key:"open",value:(a=(0,r.A)((0,i.A)().m((function e(){var t;return(0,i.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.updateComplete;case 1:return e.n=2,null===(t=this._picker)||void 0===t?void 0:t.open();case 2:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"hassSubscribe",value:function(){return[(0,b.o5)(this.hass.connection,(e=>{this._labels=e}))]}},{key:"render",value:function(){var e,t,a=null!==(e=this.placeholder)&&void 0!==e?e:this.hass.localize("ui.components.label-picker.label"),i=this._computeValueRenderer(this._labels);return(0,u.qy)(Z||(Z=L`
      <ha-generic-picker
        .disabled=${0}
        .hass=${0}
        .autofocus=${0}
        .label=${0}
        .notFoundLabel=${0}
        .emptyLabel=${0}
        .addButtonLabel=${0}
        .placeholder=${0}
        .value=${0}
        .getItems=${0}
        .getAdditionalItems=${0}
        .valueRenderer=${0}
        @value-changed=${0}
      >
        <slot .slot=${0}></slot>
      </ha-generic-picker>
    `),this.disabled,this.hass,this.autofocus,this.label,this._notFoundLabel,this.hass.localize("ui.components.label-picker.no_labels"),this.hass.localize("ui.components.label-picker.add"),a,this.value,this._getItems,this._getAdditionalItems,i,this._valueChanged,null!==(t=this._slotNodes)&&void 0!==t&&t.length?"field":void 0)}},{key:"_valueChanged",value:function(e){var t=this;e.stopPropagation();var a=e.detail.value;if(a!==C)if(a)if(a.startsWith(H)){this.hass.loadFragmentTranslation("config");var o=a.substring(13);(0,f.f)(this,{suggestedName:o,createEntry:(n=(0,r.A)((0,i.A)().m((function e(a){var r,o;return(0,i.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:return e.p=0,e.n=1,(0,b._9)(t.hass,a);case 1:r=e.v,t._setValue(r.label_id),e.n=3;break;case 2:e.p=2,o=e.v,(0,_.K$)(t,{title:t.hass.localize("ui.components.label-picker.failed_create_label"),text:o.message});case 3:return e.a(2)}}),e,null,[[0,2]])}))),function(e){return n.apply(this,arguments)})})}else{var n;this._setValue(a)}else this._setValue(void 0)}},{key:"_setValue",value:function(e){this.value=e,setTimeout((()=>{(0,v.r)(this,"value-changed",{value:e}),(0,v.r)(this,"change")}),0)}}]);var a}((0,y.E)(u.WF));(0,d.__decorate)([(0,h.MZ)({attribute:!1})],E.prototype,"hass",void 0),(0,d.__decorate)([(0,h.MZ)()],E.prototype,"label",void 0),(0,d.__decorate)([(0,h.MZ)()],E.prototype,"value",void 0),(0,d.__decorate)([(0,h.MZ)()],E.prototype,"helper",void 0),(0,d.__decorate)([(0,h.MZ)()],E.prototype,"placeholder",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean,attribute:"no-add"})],E.prototype,"noAdd",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"include-domains"})],E.prototype,"includeDomains",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"exclude-domains"})],E.prototype,"excludeDomains",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"include-device-classes"})],E.prototype,"includeDeviceClasses",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"exclude-label"})],E.prototype,"excludeLabels",void 0),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],E.prototype,"deviceFilter",void 0),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],E.prototype,"entityFilter",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean})],E.prototype,"disabled",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean})],E.prototype,"required",void 0),(0,d.__decorate)([(0,h.wk)()],E.prototype,"_labels",void 0),(0,d.__decorate)([(0,h.KN)({flatten:!0})],E.prototype,"_slotNodes",void 0),(0,d.__decorate)([(0,h.P)("ha-generic-picker")],E.prototype,"_picker",void 0),E=(0,d.__decorate)([(0,h.EM)("ha-label-picker")],E),t()}catch(S){t(S)}}))},32649:function(e,t,a){a.a(e,(async function(e,t){try{var i=a(94741),r=a(61397),o=a(50264),n=a(44734),l=a(56038),s=a(69683),c=a(6454),d=(a(52675),a(89463),a(28706),a(2008),a(74423),a(62062),a(26910),a(18111),a(22489),a(7588),a(61701),a(26099),a(42762),a(23500),a(62826)),u=a(96196),h=a(77845),p=a(4937),v=a(22786),b=a(10393),_=a(92542),y=a(25749),f=a(41327),m=a(10085),g=a(61940),k=(a(96294),a(25388),a(80990)),A=a(88422),w=e([k,A]);[k,A]=w.then?(await w)():w;var $,M,Z,L,V,x=e=>e,H=function(e){function t(){var e;(0,n.A)(this,t);for(var a=arguments.length,i=new Array(a),r=0;r<a;r++)i[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(i))).noAdd=!1,e.disabled=!1,e.required=!1,e._sortedLabels=(0,v.A)(((e,t,a)=>null==e?void 0:e.map((e=>null==t?void 0:t[e])).sort(((e,t)=>(0,y.xL)((null==e?void 0:e.name)||"",(null==t?void 0:t.name)||"",a))))),e}return(0,c.A)(t,e),(0,l.A)(t,[{key:"open",value:(d=(0,o.A)((0,r.A)().m((function e(){var t;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.updateComplete;case 1:return e.n=2,null===(t=this.labelPicker)||void 0===t?void 0:t.open();case 2:return e.a(2)}}),e,this)}))),function(){return d.apply(this,arguments)})},{key:"focus",value:(a=(0,o.A)((0,r.A)().m((function e(){var t;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.updateComplete;case 1:return e.n=2,null===(t=this.labelPicker)||void 0===t?void 0:t.focus();case 2:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"hassSubscribe",value:function(){return[(0,f.o5)(this.hass.connection,(e=>{var t={};e.forEach((e=>{t[e.label_id]=e})),this._labels=t}))]}},{key:"render",value:function(){var e=this._sortedLabels(this.value,this._labels,this.hass.locale.language);return(0,u.qy)($||($=x`
      ${0}
      <ha-label-picker
        .hass=${0}
        .helper=${0}
        .disabled=${0}
        .required=${0}
        .placeholder=${0}
        .excludeLabels=${0}
        @value-changed=${0}
      >
        <ha-chip-set>
          ${0}
          <ha-button
            id="picker"
            size="small"
            appearance="filled"
            @click=${0}
            .disabled=${0}
          >
            <ha-svg-icon .path=${0} slot="start"></ha-svg-icon>
            ${0}
          </ha-button>
        </ha-chip-set>
      </ha-label-picker>
    `),this.label?(0,u.qy)(M||(M=x`<label>${0}</label>`),this.label):u.s6,this.hass,this.helper,this.disabled,this.required,this.placeholder,this.value,this._labelChanged,null!=e&&e.length?(0,p.u)(e,(e=>null==e?void 0:e.label_id),(e=>{var t,a=null!=e&&e.color?(0,b.M)(e.color):void 0,i="label-"+e.label_id;return(0,u.qy)(Z||(Z=x`
                    <ha-tooltip
                      .for=${0}
                      .disabled=${0}
                    >
                      ${0}
                    </ha-tooltip>
                    <ha-input-chip
                      .item=${0}
                      .id=${0}
                      @remove=${0}
                      @click=${0}
                      .disabled=${0}
                      .label=${0}
                      selected
                      style=${0}
                    >
                      ${0}
                    </ha-input-chip>
                  `),i,!(null!=e&&null!==(t=e.description)&&void 0!==t&&t.trim()),null==e?void 0:e.description,e,i,this._removeItem,this._openDetail,this.disabled,null==e?void 0:e.name,a?`--color: ${a}`:"",null!=e&&e.icon?(0,u.qy)(L||(L=x`<ha-icon
                            slot="icon"
                            .icon=${0}
                          ></ha-icon>`),e.icon):u.s6)})):u.s6,this._openPicker,this.disabled,"M3 16H10V14H3M18 14V10H16V14H12V16H16V20H18V16H22V14M14 6H3V8H14M14 10H3V12H14V10Z",this.hass.localize("ui.components.label-picker.add"))}},{key:"_value",get:function(){return this.value||[]}},{key:"_removeItem",value:function(e){var t=e.currentTarget.item;this._setValue(this._value.filter((e=>e!==t.label_id)))}},{key:"_openDetail",value:function(e){var t,a=this,i=e.currentTarget.item;(0,g.f)(this,{entry:i,updateEntry:(t=(0,o.A)((0,r.A)().m((function e(t){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,f.Rp)(a.hass,i.label_id,t);case 1:return e.a(2)}}),e)}))),function(e){return t.apply(this,arguments)})})}},{key:"_labelChanged",value:function(e){e.stopPropagation();var t=e.detail.value;t&&!this._value.includes(t)&&(this._setValue([].concat((0,i.A)(this._value),[t])),this.labelPicker.value="")}},{key:"_setValue",value:function(e){this.value=e,setTimeout((()=>{(0,_.r)(this,"value-changed",{value:e}),(0,_.r)(this,"change")}),0)}},{key:"_openPicker",value:function(e){e.stopPropagation(),this.labelPicker.open()}}]);var a,d}((0,m.E)(u.WF));H.styles=(0,u.AH)(V||(V=x`
    ha-chip-set {
      margin-bottom: 8px;
      background-color: var(--mdc-text-field-fill-color);
      border-bottom: 1px solid var(--ha-color-border-neutral-normal);
      border-top-right-radius: var(--ha-border-radius-sm);
      border-top-left-radius: var(--ha-border-radius-sm);
      padding: var(--ha-space-3);
    }
    .placeholder {
      color: var(--mdc-text-field-label-ink-color);
      display: flex;
      align-items: center;
      height: var(--ha-space-8);
    }
    ha-input-chip {
      --md-input-chip-selected-container-color: var(--color, var(--grey-color));
      --ha-input-chip-selected-container-opacity: 0.5;
      --md-input-chip-selected-outline-width: 1px;
    }
    label {
      display: block;
      margin: 0 0 8px;
    }
  `)),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],H.prototype,"hass",void 0),(0,d.__decorate)([(0,h.MZ)()],H.prototype,"label",void 0),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],H.prototype,"value",void 0),(0,d.__decorate)([(0,h.MZ)()],H.prototype,"helper",void 0),(0,d.__decorate)([(0,h.MZ)()],H.prototype,"placeholder",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean,attribute:"no-add"})],H.prototype,"noAdd",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"include-domains"})],H.prototype,"includeDomains",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"exclude-domains"})],H.prototype,"excludeDomains",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"include-device-classes"})],H.prototype,"includeDeviceClasses",void 0),(0,d.__decorate)([(0,h.MZ)({type:Array,attribute:"exclude-label"})],H.prototype,"excludeLabels",void 0),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],H.prototype,"deviceFilter",void 0),(0,d.__decorate)([(0,h.MZ)({attribute:!1})],H.prototype,"entityFilter",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean})],H.prototype,"disabled",void 0),(0,d.__decorate)([(0,h.MZ)({type:Boolean})],H.prototype,"required",void 0),(0,d.__decorate)([(0,h.wk)()],H.prototype,"_labels",void 0),(0,d.__decorate)([(0,h.P)("ha-label-picker",!0)],H.prototype,"labelPicker",void 0),H=(0,d.__decorate)([(0,h.EM)("ha-labels-picker")],H),t()}catch(C){t(C)}}))},88422:function(e,t,a){a.a(e,(async function(e,t){try{var i=a(44734),r=a(56038),o=a(69683),n=a(6454),l=(a(28706),a(2892),a(62826)),s=a(52630),c=a(96196),d=a(77845),u=e([s]);s=(u.then?(await u)():u)[0];var h,p=e=>e,v=function(e){function t(){var e;(0,i.A)(this,t);for(var a=arguments.length,r=new Array(a),n=0;n<a;n++)r[n]=arguments[n];return(e=(0,o.A)(this,t,[].concat(r))).showDelay=150,e.hideDelay=150,e}return(0,n.A)(t,e),(0,r.A)(t,null,[{key:"styles",get:function(){return[s.A.styles,(0,c.AH)(h||(h=p`
        :host {
          --wa-tooltip-background-color: var(--secondary-background-color);
          --wa-tooltip-content-color: var(--primary-text-color);
          --wa-tooltip-font-family: var(
            --ha-tooltip-font-family,
            var(--ha-font-family-body)
          );
          --wa-tooltip-font-size: var(
            --ha-tooltip-font-size,
            var(--ha-font-size-s)
          );
          --wa-tooltip-font-weight: var(
            --ha-tooltip-font-weight,
            var(--ha-font-weight-normal)
          );
          --wa-tooltip-line-height: var(
            --ha-tooltip-line-height,
            var(--ha-line-height-condensed)
          );
          --wa-tooltip-padding: 8px;
          --wa-tooltip-border-radius: var(
            --ha-tooltip-border-radius,
            var(--ha-border-radius-sm)
          );
          --wa-tooltip-arrow-size: var(--ha-tooltip-arrow-size, 8px);
          --wa-z-index-tooltip: var(--ha-tooltip-z-index, 1000);
        }
      `))]}}])}(s.A);(0,l.__decorate)([(0,d.MZ)({attribute:"show-delay",type:Number})],v.prototype,"showDelay",void 0),(0,l.__decorate)([(0,d.MZ)({attribute:"hide-delay",type:Number})],v.prototype,"hideDelay",void 0),v=(0,l.__decorate)([(0,d.EM)("ha-tooltip")],v),t()}catch(b){t(b)}}))},41327:function(e,t,a){a.d(t,{IV:function(){return p},Rp:function(){return h},_9:function(){return u},o5:function(){return d}});a(52675),a(89463),a(28706),a(2008),a(74423),a(23792),a(62062),a(26910),a(18111),a(81148),a(22489),a(7588),a(61701),a(13579),a(26099),a(16034),a(31415),a(17642),a(58004),a(33853),a(45876),a(32475),a(15024),a(31698),a(23500),a(62953);var i=a(70570),r=a(41144),o=a(25749),n=a(40404),l=a(1491),s=e=>e.sendMessagePromise({type:"config/label_registry/list"}).then((e=>e.sort(((e,t)=>(0,o.xL)(e.name,t.name))))),c=(e,t)=>e.subscribeEvents((0,n.s)((()=>s(e).then((e=>t.setState(e,!0)))),500,!0),"label_registry_updated"),d=(e,t)=>(0,i.N)("_labelRegistry",s,c,e,t),u=(e,t)=>e.callWS(Object.assign({type:"config/label_registry/create"},t)),h=(e,t,a)=>e.callWS(Object.assign({type:"config/label_registry/update",label_id:t},a)),p=function(e,t,a,i,o,n,s,c,d,u,h){var p=arguments.length>11&&void 0!==arguments[11]?arguments[11]:"";if(!o||0===o.length)return[];var v,b,_=Object.values(a),y=Object.values(i),f={};(n||s||c||d||u)&&(f=(0,l.g2)(y),v=_,b=y.filter((e=>e.labels.length>0)),n&&(v=v.filter((e=>{var t=f[e.id];return!(!t||!t.length)&&f[e.id].some((e=>n.includes((0,r.m)(e.entity_id))))})),b=b.filter((e=>n.includes((0,r.m)(e.entity_id))))),s&&(v=v.filter((e=>{var t=f[e.id];return!t||!t.length||y.every((e=>!s.includes((0,r.m)(e.entity_id))))})),b=b.filter((e=>!s.includes((0,r.m)(e.entity_id))))),c&&(v=v.filter((t=>{var a=f[t.id];return!(!a||!a.length)&&f[t.id].some((t=>{var a=e[t.entity_id];return!!a&&(a.attributes.device_class&&c.includes(a.attributes.device_class))}))})),b=b.filter((t=>{var a=e[t.entity_id];return a&&a.attributes.device_class&&c.includes(a.attributes.device_class)}))),d&&(v=v.filter((e=>d(e)))),u&&(v=v.filter((t=>{var a=f[t.id];return!(!a||!a.length)&&f[t.id].some((t=>{var a=e[t.entity_id];return!!a&&u(a)}))})),b=b.filter((t=>{var a=e[t.entity_id];return!!a&&u(a)}))));var m,g=o,k=new Set;return v&&(m=v.filter((e=>e.area_id)).map((e=>e.area_id)),v.forEach((e=>{e.labels.forEach((e=>k.add(e)))}))),b&&(m=(null!=m?m:[]).concat(b.filter((e=>e.area_id)).map((e=>e.area_id))),b.forEach((e=>{e.labels.forEach((e=>k.add(e)))}))),m&&m.forEach((e=>{var a=t[e];null==a||a.labels.forEach((e=>k.add(e)))})),h&&(g=g.filter((e=>!h.includes(e.label_id)))),(v||b)&&(g=g.filter((e=>k.has(e.label_id)))),g.map((e=>{var t;return{id:`${p}${e.label_id}`,primary:e.name,secondary:null!==(t=e.description)&&void 0!==t?t:"",icon:e.icon||void 0,icon_path:e.icon?void 0:"M17.63,5.84C17.27,5.33 16.67,5 16,5H5A2,2 0 0,0 3,7V17A2,2 0 0,0 5,19H16C16.67,19 17.27,18.66 17.63,18.15L22,12L17.63,5.84Z",sorting_label:e.name,search_labels:[e.name,e.label_id,e.description].filter((e=>Boolean(e)))}}))}},10085:function(e,t,a){a.d(t,{E:function(){return u}});var i=a(31432),r=a(44734),o=a(56038),n=a(69683),l=a(25460),s=a(6454),c=(a(74423),a(23792),a(18111),a(13579),a(26099),a(3362),a(62953),a(62826)),d=a(77845),u=e=>{var t=function(e){function t(){return(0,r.A)(this,t),(0,n.A)(this,t,arguments)}return(0,s.A)(t,e),(0,o.A)(t,[{key:"connectedCallback",value:function(){(0,l.A)(t,"connectedCallback",this,3)([]),this._checkSubscribed()}},{key:"disconnectedCallback",value:function(){if((0,l.A)(t,"disconnectedCallback",this,3)([]),this.__unsubs){for(;this.__unsubs.length;){var e=this.__unsubs.pop();e instanceof Promise?e.then((e=>e())):e()}this.__unsubs=void 0}}},{key:"updated",value:function(e){if((0,l.A)(t,"updated",this,3)([e]),e.has("hass"))this._checkSubscribed();else if(this.hassSubscribeRequiredHostProps){var a,r=(0,i.A)(e.keys());try{for(r.s();!(a=r.n()).done;){var o=a.value;if(this.hassSubscribeRequiredHostProps.includes(o))return void this._checkSubscribed()}}catch(n){r.e(n)}finally{r.f()}}}},{key:"hassSubscribe",value:function(){return[]}},{key:"_checkSubscribed",value:function(){var e;void 0!==this.__unsubs||!this.isConnected||void 0===this.hass||null!==(e=this.hassSubscribeRequiredHostProps)&&void 0!==e&&e.some((e=>void 0===this[e]))||(this.__unsubs=this.hassSubscribe())}}])}(e);return(0,c.__decorate)([(0,d.MZ)({attribute:!1})],t.prototype,"hass",void 0),t}},61940:function(e,t,a){a.d(t,{f:function(){return o}});a(23792),a(26099),a(3362),a(62953);var i=a(92542),r=()=>a.e("7841").then(a.bind(a,11064)),o=(e,t)=>{(0,i.r)(e,"show-dialog",{dialogTag:"dialog-label-detail",dialogImport:r,dialogParams:t})}},70570:function(e,t,a){a.d(t,{N:function(){return o}});a(16280),a(44114),a(26099),a(3362);var i=e=>{var t=[];function a(a,i){e=i?a:Object.assign(Object.assign({},e),a);for(var r=t,o=0;o<r.length;o++)r[o](e)}return{get state(){return e},action(t){function i(e){a(e,!1)}return function(){for(var a=[e],r=0;r<arguments.length;r++)a.push(arguments[r]);var o=t.apply(this,a);if(null!=o)return o instanceof Promise?o.then(i):i(o)}},setState:a,clearState(){e=void 0},subscribe(e){return t.push(e),()=>{!function(e){for(var a=[],i=0;i<t.length;i++)t[i]===e?e=null:a.push(t[i]);t=a}(e)}}}},r=function(e,t,a,r){var o=arguments.length>4&&void 0!==arguments[4]?arguments[4]:{unsubGrace:!0};if(e[t])return e[t];var n,l,s=0,c=i(),d=()=>{if(!a)throw new Error("Collection does not support refresh");return a(e).then((e=>c.setState(e,!0)))},u=()=>d().catch((t=>{if(e.connected)throw t})),h=()=>{l=void 0,n&&n.then((e=>{e()})),c.clearState(),e.removeEventListener("ready",d),e.removeEventListener("disconnected",p)},p=()=>{l&&(clearTimeout(l),h())};return e[t]={get state(){return c.state},refresh:d,subscribe(t){1===++s&&(()=>{if(void 0!==l)return clearTimeout(l),void(l=void 0);r&&(n=r(e,c)),a&&(e.addEventListener("ready",u),u()),e.addEventListener("disconnected",p)})();var i=c.subscribe(t);return void 0!==c.state&&setTimeout((()=>t(c.state)),0),()=>{i(),--s||(o.unsubGrace?l=setTimeout(h,5e3):h())}}},e[t]},o=(e,t,a,i,o)=>r(i,e,t,a).subscribe(o)}}]);
//# sourceMappingURL=7298.c6086a7fb7ec7796.js.map