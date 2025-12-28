/*! For license information please see 9936.df87a7a5c04c2121.js.LICENSE.txt */
"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["9936"],{32637:function(e,t,i){i.a(e,(async function(e,t){try{var n=i(61397),r=i(50264),s=i(94741),a=i(44734),o=i(56038),u=i(69683),c=i(6454),l=(i(28706),i(2008),i(74423),i(62062),i(54554),i(18111),i(22489),i(61701),i(26099),i(62826)),d=i(96196),h=i(77845),v=i(22786),y=i(92542),p=i(45996),f=(i(63801),i(82965)),_=e([f]);f=(_.then?(await _)():_)[0];var $,b,m,A,k,g=e=>e,E=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,n=new Array(i),r=0;r<i;r++)n[r]=arguments[r];return(e=(0,u.A)(this,t,[].concat(n))).disabled=!1,e.required=!1,e.reorder=!1,e._excludeEntities=(0,v.A)(((e,t)=>void 0===e?t:[].concat((0,s.A)(t||[]),(0,s.A)(e)))),e}return(0,c.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){if(!this.hass)return d.s6;var e=this._currentEntities;return(0,d.qy)($||($=g`
      ${0}
      <ha-sortable
        .disabled=${0}
        handle-selector=".entity-handle"
        @item-moved=${0}
      >
        <div class="list">
          ${0}
        </div>
      </ha-sortable>
      <div>
        <ha-entity-picker
          allow-custom-entity
          .hass=${0}
          .includeDomains=${0}
          .excludeDomains=${0}
          .includeEntities=${0}
          .excludeEntities=${0}
          .includeDeviceClasses=${0}
          .includeUnitOfMeasurement=${0}
          .entityFilter=${0}
          .placeholder=${0}
          .helper=${0}
          .disabled=${0}
          .createDomains=${0}
          .required=${0}
          @value-changed=${0}
          .addButton=${0}
        ></ha-entity-picker>
      </div>
    `),this.label?(0,d.qy)(b||(b=g`<label>${0}</label>`),this.label):d.s6,!this.reorder||this.disabled,this._entityMoved,e.map((e=>(0,d.qy)(m||(m=g`
              <div class="entity">
                <ha-entity-picker
                  allow-custom-entity
                  .curValue=${0}
                  .hass=${0}
                  .includeDomains=${0}
                  .excludeDomains=${0}
                  .includeEntities=${0}
                  .excludeEntities=${0}
                  .includeDeviceClasses=${0}
                  .includeUnitOfMeasurement=${0}
                  .entityFilter=${0}
                  .value=${0}
                  .disabled=${0}
                  .createDomains=${0}
                  @value-changed=${0}
                ></ha-entity-picker>
                ${0}
              </div>
            `),e,this.hass,this.includeDomains,this.excludeDomains,this.includeEntities,this.excludeEntities,this.includeDeviceClasses,this.includeUnitOfMeasurement,this.entityFilter,e,this.disabled,this.createDomains,this._entityChanged,this.reorder?(0,d.qy)(A||(A=g`
                      <ha-svg-icon
                        class="entity-handle"
                        .path=${0}
                      ></ha-svg-icon>
                    `),"M21 11H3V9H21V11M21 13H3V15H21V13Z"):d.s6))),this.hass,this.includeDomains,this.excludeDomains,this.includeEntities,this._excludeEntities(this.value,this.excludeEntities),this.includeDeviceClasses,this.includeUnitOfMeasurement,this.entityFilter,this.placeholder,this.helper,this.disabled,this.createDomains,this.required&&!e.length,this._addEntity,e.length>0)}},{key:"_entityMoved",value:function(e){e.stopPropagation();var t=e.detail,i=t.oldIndex,n=t.newIndex,r=this._currentEntities,a=r[i],o=(0,s.A)(r);o.splice(i,1),o.splice(n,0,a),this._updateEntities(o)}},{key:"_currentEntities",get:function(){return this.value||[]}},{key:"_updateEntities",value:(l=(0,r.A)((0,n.A)().m((function e(t){return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:this.value=t,(0,y.r)(this,"value-changed",{value:t});case 1:return e.a(2)}}),e,this)}))),function(e){return l.apply(this,arguments)})},{key:"_entityChanged",value:function(e){e.stopPropagation();var t=e.currentTarget.curValue,i=e.detail.value;if(i!==t&&(void 0===i||(0,p.n)(i))){var n=this._currentEntities;i&&!n.includes(i)?this._updateEntities(n.map((e=>e===t?i:e))):this._updateEntities(n.filter((e=>e!==t)))}}},{key:"_addEntity",value:(i=(0,r.A)((0,n.A)().m((function e(t){var i,r;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:if(t.stopPropagation(),i=t.detail.value){e.n=1;break}return e.a(2);case 1:if(t.currentTarget.value="",i){e.n=2;break}return e.a(2);case 2:if(!(r=this._currentEntities).includes(i)){e.n=3;break}return e.a(2);case 3:this._updateEntities([].concat((0,s.A)(r),[i]));case 4:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})}]);var i,l}(d.WF);E.styles=(0,d.AH)(k||(k=g`
    div {
      margin-top: 8px;
    }
    label {
      display: block;
      margin: 0 0 8px;
    }
    .entity {
      display: flex;
      flex-direction: row;
      align-items: center;
    }
    .entity ha-entity-picker {
      flex: 1;
    }
    .entity-handle {
      padding: 8px;
      cursor: move; /* fallback if grab cursor is unsupported */
      cursor: grab;
    }
  `)),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],E.prototype,"hass",void 0),(0,l.__decorate)([(0,h.MZ)({type:Array})],E.prototype,"value",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],E.prototype,"disabled",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],E.prototype,"required",void 0),(0,l.__decorate)([(0,h.MZ)()],E.prototype,"label",void 0),(0,l.__decorate)([(0,h.MZ)()],E.prototype,"placeholder",void 0),(0,l.__decorate)([(0,h.MZ)()],E.prototype,"helper",void 0),(0,l.__decorate)([(0,h.MZ)({type:Array,attribute:"include-domains"})],E.prototype,"includeDomains",void 0),(0,l.__decorate)([(0,h.MZ)({type:Array,attribute:"exclude-domains"})],E.prototype,"excludeDomains",void 0),(0,l.__decorate)([(0,h.MZ)({type:Array,attribute:"include-device-classes"})],E.prototype,"includeDeviceClasses",void 0),(0,l.__decorate)([(0,h.MZ)({type:Array,attribute:"include-unit-of-measurement"})],E.prototype,"includeUnitOfMeasurement",void 0),(0,l.__decorate)([(0,h.MZ)({type:Array,attribute:"include-entities"})],E.prototype,"includeEntities",void 0),(0,l.__decorate)([(0,h.MZ)({type:Array,attribute:"exclude-entities"})],E.prototype,"excludeEntities",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],E.prototype,"entityFilter",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:!1,type:Array})],E.prototype,"createDomains",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],E.prototype,"reorder",void 0),E=(0,l.__decorate)([(0,h.EM)("ha-entities-picker")],E),t()}catch(w){t(w)}}))},25394:function(e,t,i){i.a(e,(async function(e,n){try{i.r(t),i.d(t,{HaEntitySelector:function(){return k}});var r=i(44734),s=i(56038),a=i(69683),o=i(6454),u=i(25460),c=(i(28706),i(2008),i(18111),i(22489),i(13579),i(26099),i(62826)),l=i(96196),d=i(77845),h=i(55376),v=i(92542),y=i(28441),p=i(82694),f=i(32637),_=i(82965),$=e([f,_]);[f,_]=$.then?(await $)():$;var b,m,A=e=>e,k=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,n=new Array(i),s=0;s<i;s++)n[s]=arguments[s];return(e=(0,a.A)(this,t,[].concat(n))).disabled=!1,e.required=!0,e._filterEntities=t=>{var i;return null===(i=e.selector)||void 0===i||null===(i=i.entity)||void 0===i||!i.filter||(0,h.e)(e.selector.entity.filter).some((i=>(0,p.Ru)(i,t,e._entitySources)))},e}return(0,o.A)(t,e),(0,s.A)(t,[{key:"_hasIntegration",value:function(e){var t;return(null===(t=e.entity)||void 0===t?void 0:t.filter)&&(0,h.e)(e.entity.filter).some((e=>e.integration))}},{key:"willUpdate",value:function(e){var t,i;e.get("selector")&&void 0!==this.value&&(null!==(t=this.selector.entity)&&void 0!==t&&t.multiple&&!Array.isArray(this.value)?(this.value=[this.value],(0,v.r)(this,"value-changed",{value:this.value})):null!==(i=this.selector.entity)&&void 0!==i&&i.multiple||!Array.isArray(this.value)||(this.value=this.value[0],(0,v.r)(this,"value-changed",{value:this.value})))}},{key:"render",value:function(){var e,t,i,n;return this._hasIntegration(this.selector)&&!this._entitySources?l.s6:null!==(e=this.selector.entity)&&void 0!==e&&e.multiple?(0,l.qy)(m||(m=A`
      <ha-entities-picker
        .hass=${0}
        .value=${0}
        .label=${0}
        .helper=${0}
        .includeEntities=${0}
        .excludeEntities=${0}
        .reorder=${0}
        .entityFilter=${0}
        .createDomains=${0}
        .placeholder=${0}
        .disabled=${0}
        .required=${0}
      ></ha-entities-picker>
    `),this.hass,this.value,this.label,this.helper,this.selector.entity.include_entities,this.selector.entity.exclude_entities,null!==(t=this.selector.entity.reorder)&&void 0!==t&&t,this._filterEntities,this._createDomains,this.placeholder,this.disabled,this.required):(0,l.qy)(b||(b=A`<ha-entity-picker
        .hass=${0}
        .value=${0}
        .label=${0}
        .helper=${0}
        .includeEntities=${0}
        .excludeEntities=${0}
        .entityFilter=${0}
        .createDomains=${0}
        .placeholder=${0}
        .disabled=${0}
        .required=${0}
        allow-custom-entity
      ></ha-entity-picker>`),this.hass,this.value,this.label,this.helper,null===(i=this.selector.entity)||void 0===i?void 0:i.include_entities,null===(n=this.selector.entity)||void 0===n?void 0:n.exclude_entities,this._filterEntities,this._createDomains,this.placeholder,this.disabled,this.required)}},{key:"updated",value:function(e){(0,u.A)(t,"updated",this,3)([e]),e.has("selector")&&this._hasIntegration(this.selector)&&!this._entitySources&&(0,y.c)(this.hass).then((e=>{this._entitySources=e})),e.has("selector")&&(this._createDomains=(0,p.Lo)(this.selector))}}])}(l.WF);(0,c.__decorate)([(0,d.MZ)({attribute:!1})],k.prototype,"hass",void 0),(0,c.__decorate)([(0,d.MZ)({attribute:!1})],k.prototype,"selector",void 0),(0,c.__decorate)([(0,d.wk)()],k.prototype,"_entitySources",void 0),(0,c.__decorate)([(0,d.MZ)()],k.prototype,"value",void 0),(0,c.__decorate)([(0,d.MZ)()],k.prototype,"label",void 0),(0,c.__decorate)([(0,d.MZ)()],k.prototype,"helper",void 0),(0,c.__decorate)([(0,d.MZ)()],k.prototype,"placeholder",void 0),(0,c.__decorate)([(0,d.MZ)({type:Boolean})],k.prototype,"disabled",void 0),(0,c.__decorate)([(0,d.MZ)({type:Boolean})],k.prototype,"required",void 0),(0,c.__decorate)([(0,d.wk)()],k.prototype,"_createDomains",void 0),k=(0,c.__decorate)([(0,d.EM)("ha-selector-entity")],k),n()}catch(g){n(g)}}))},28441:function(e,t,i){i.d(t,{c:function(){return o}});var n=i(61397),r=i(50264),s=(i(28706),i(26099),i(3362),function(){var e=(0,r.A)((0,n.A)().m((function e(t,i,r,a,o){var u,c,l,d,h,v,y,p=arguments;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:for(u=p.length,c=new Array(u>5?u-5:0),l=5;l<u;l++)c[l-5]=p[l];if(h=(d=o)[t],v=e=>a&&a(o,e.result)!==e.cacheKey?(d[t]=void 0,s.apply(void 0,[t,i,r,a,o].concat(c))):e.result,!h){e.n=1;break}return e.a(2,h instanceof Promise?h.then(v):v(h));case 1:return y=r.apply(void 0,[o].concat(c)),d[t]=y,y.then((e=>{d[t]={result:e,cacheKey:null==a?void 0:a(o,e)},setTimeout((()=>{d[t]=void 0}),i)}),(()=>{d[t]=void 0})),e.a(2,y)}}),e)})));return function(t,i,n,r,s){return e.apply(this,arguments)}}()),a=e=>e.callWS({type:"entity/source"}),o=e=>s("_entitySources",3e4,a,(e=>Object.keys(e.states).length),e)},70570:function(e,t,i){i.d(t,{N:function(){return s}});i(16280),i(44114),i(26099),i(3362);var n=e=>{var t=[];function i(i,n){e=n?i:Object.assign(Object.assign({},e),i);for(var r=t,s=0;s<r.length;s++)r[s](e)}return{get state(){return e},action(t){function n(e){i(e,!1)}return function(){for(var i=[e],r=0;r<arguments.length;r++)i.push(arguments[r]);var s=t.apply(this,i);if(null!=s)return s instanceof Promise?s.then(n):n(s)}},setState:i,clearState(){e=void 0},subscribe(e){return t.push(e),()=>{!function(e){for(var i=[],n=0;n<t.length;n++)t[n]===e?e=null:i.push(t[n]);t=i}(e)}}}},r=function(e,t,i,r){var s=arguments.length>4&&void 0!==arguments[4]?arguments[4]:{unsubGrace:!0};if(e[t])return e[t];var a,o,u=0,c=n(),l=()=>{if(!i)throw new Error("Collection does not support refresh");return i(e).then((e=>c.setState(e,!0)))},d=()=>l().catch((t=>{if(e.connected)throw t})),h=()=>{o=void 0,a&&a.then((e=>{e()})),c.clearState(),e.removeEventListener("ready",l),e.removeEventListener("disconnected",v)},v=()=>{o&&(clearTimeout(o),h())};return e[t]={get state(){return c.state},refresh:l,subscribe(t){1===++u&&(()=>{if(void 0!==o)return clearTimeout(o),void(o=void 0);r&&(a=r(e,c)),i&&(e.addEventListener("ready",d),d()),e.addEventListener("disconnected",v)})();var n=c.subscribe(t);return void 0!==c.state&&setTimeout((()=>t(c.state)),0),()=>{n(),--u||(s.unsubGrace?o=setTimeout(h,5e3):h())}}},e[t]},s=(e,t,i,n,s)=>r(n,e,t,i).subscribe(s)},45847:function(e,t,i){i.d(t,{T:function(){return b}});var n=i(61397),r=i(50264),s=i(44734),a=i(56038),o=i(75864),u=i(69683),c=i(6454),l=(i(50113),i(25276),i(18111),i(20116),i(26099),i(3362),i(4610)),d=i(63937),h=i(37540);i(52675),i(89463),i(66412),i(16280),i(23792),i(62953);var v=function(){return(0,a.A)((function e(t){(0,s.A)(this,e),this.G=t}),[{key:"disconnect",value:function(){this.G=void 0}},{key:"reconnect",value:function(e){this.G=e}},{key:"deref",value:function(){return this.G}}])}(),y=function(){return(0,a.A)((function e(){(0,s.A)(this,e),this.Y=void 0,this.Z=void 0}),[{key:"get",value:function(){return this.Y}},{key:"pause",value:function(){var e;null!==(e=this.Y)&&void 0!==e||(this.Y=new Promise((e=>this.Z=e)))}},{key:"resume",value:function(){var e;null!==(e=this.Z)&&void 0!==e&&e.call(this),this.Y=this.Z=void 0}}])}(),p=i(42017),f=e=>!(0,d.sO)(e)&&"function"==typeof e.then,_=1073741823,$=function(e){function t(){var e;return(0,s.A)(this,t),(e=(0,u.A)(this,t,arguments))._$Cwt=_,e._$Cbt=[],e._$CK=new v((0,o.A)(e)),e._$CX=new y,e}return(0,c.A)(t,e),(0,a.A)(t,[{key:"render",value:function(){for(var e,t=arguments.length,i=new Array(t),n=0;n<t;n++)i[n]=arguments[n];return null!==(e=i.find((e=>!f(e))))&&void 0!==e?e:l.c0}},{key:"update",value:function(e,t){var i=this,s=this._$Cbt,a=s.length;this._$Cbt=t;var o=this._$CK,u=this._$CX;this.isConnected||this.disconnected();for(var c,d=function(){var e=t[h];if(!f(e))return{v:(i._$Cwt=h,e)};h<a&&e===s[h]||(i._$Cwt=_,a=0,Promise.resolve(e).then(function(){var t=(0,r.A)((0,n.A)().m((function t(i){var r,s;return(0,n.A)().w((function(t){for(;;)switch(t.n){case 0:if(!u.get()){t.n=2;break}return t.n=1,u.get();case 1:t.n=0;break;case 2:void 0!==(r=o.deref())&&(s=r._$Cbt.indexOf(e))>-1&&s<r._$Cwt&&(r._$Cwt=s,r.setValue(i));case 3:return t.a(2)}}),t)})));return function(e){return t.apply(this,arguments)}}()))},h=0;h<t.length&&!(h>this._$Cwt);h++)if(c=d())return c.v;return l.c0}},{key:"disconnected",value:function(){this._$CK.disconnect(),this._$CX.pause()}},{key:"reconnected",value:function(){this._$CK.reconnect(this),this._$CX.resume()}}])}(h.Kq),b=(0,p.u$)($)}}]);
//# sourceMappingURL=9936.df87a7a5c04c2121.js.map