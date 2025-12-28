"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["4924"],{56934:function(e,t,o){o.a(e,(async function(e,t){try{var r=o(61397),a=o(50264),n=o(44734),i=o(56038),s=o(69683),d=o(6454),u=(o(28706),o(2008),o(26910),o(18111),o(22489),o(26099),o(62826)),c=o(96196),l=o(77845),h=o(92209),p=o(92542),v=o(25749),f=o(34402),_=(o(17963),o(55179)),y=(o(94343),e([_]));_=(y.then?(await y)():y)[0];var b,m,k,A,g=e=>e,$=e=>(0,c.qy)(b||(b=g`
  <ha-combo-box-item type="button">
    <span slot="headline">${0}</span>
    <span slot="supporting-text">${0}</span>
    ${0}
  </ha-combo-box-item>
`),e.name,e.slug,e.icon?(0,c.qy)(m||(m=g`
          <img
            alt=""
            slot="start"
            .src="/api/hassio/addons/${0}/icon"
          />
        `),e.slug):c.s6),w=function(e){function t(){var e;(0,n.A)(this,t);for(var o=arguments.length,r=new Array(o),a=0;a<o;a++)r[a]=arguments[a];return(e=(0,s.A)(this,t,[].concat(r))).value="",e.disabled=!1,e.required=!1,e}return(0,d.A)(t,e),(0,i.A)(t,[{key:"open",value:function(){var e;null===(e=this._comboBox)||void 0===e||e.open()}},{key:"focus",value:function(){var e;null===(e=this._comboBox)||void 0===e||e.focus()}},{key:"firstUpdated",value:function(){this._getAddons()}},{key:"render",value:function(){return this._error?(0,c.qy)(k||(k=g`<ha-alert alert-type="error">${0}</ha-alert>`),this._error):this._addons?(0,c.qy)(A||(A=g`
      <ha-combo-box
        .hass=${0}
        .label=${0}
        .value=${0}
        .required=${0}
        .disabled=${0}
        .helper=${0}
        .renderer=${0}
        .items=${0}
        item-value-path="slug"
        item-id-path="slug"
        item-label-path="name"
        @value-changed=${0}
      ></ha-combo-box>
    `),this.hass,void 0===this.label&&this.hass?this.hass.localize("ui.components.addon-picker.addon"):this.label,this._value,this.required,this.disabled,this.helper,$,this._addons,this._addonChanged):c.s6}},{key:"_getAddons",value:(o=(0,a.A)((0,r.A)().m((function e(){var t;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(e.p=0,!(0,h.x)(this.hass,"hassio")){e.n=2;break}return e.n=1,(0,f.b3)(this.hass);case 1:t=e.v,this._addons=t.addons.filter((e=>e.version)).sort(((e,t)=>(0,v.xL)(e.name,t.name,this.hass.locale.language))),e.n=3;break;case 2:this._error=this.hass.localize("ui.components.addon-picker.error.no_supervisor");case 3:e.n=5;break;case 4:e.p=4,e.v,this._error=this.hass.localize("ui.components.addon-picker.error.fetch_addons");case 5:return e.a(2)}}),e,this,[[0,4]])}))),function(){return o.apply(this,arguments)})},{key:"_value",get:function(){return this.value||""}},{key:"_addonChanged",value:function(e){e.stopPropagation();var t=e.detail.value;t!==this._value&&this._setValue(t)}},{key:"_setValue",value:function(e){this.value=e,setTimeout((()=>{(0,p.r)(this,"value-changed",{value:e}),(0,p.r)(this,"change")}),0)}}]);var o}(c.WF);(0,u.__decorate)([(0,l.MZ)()],w.prototype,"label",void 0),(0,u.__decorate)([(0,l.MZ)()],w.prototype,"value",void 0),(0,u.__decorate)([(0,l.MZ)()],w.prototype,"helper",void 0),(0,u.__decorate)([(0,l.wk)()],w.prototype,"_addons",void 0),(0,u.__decorate)([(0,l.MZ)({type:Boolean})],w.prototype,"disabled",void 0),(0,u.__decorate)([(0,l.MZ)({type:Boolean})],w.prototype,"required",void 0),(0,u.__decorate)([(0,l.P)("ha-combo-box")],w.prototype,"_comboBox",void 0),(0,u.__decorate)([(0,l.wk)()],w.prototype,"_error",void 0),w=(0,u.__decorate)([(0,l.EM)("ha-addon-picker")],w),t()}catch(x){t(x)}}))},19687:function(e,t,o){o.a(e,(async function(e,r){try{o.r(t),o.d(t,{HaAddonSelector:function(){return _}});var a=o(44734),n=o(56038),i=o(69683),s=o(6454),d=(o(28706),o(62826)),u=o(96196),c=o(77845),l=o(56934),h=e([l]);l=(h.then?(await h)():h)[0];var p,v,f=e=>e,_=function(e){function t(){var e;(0,a.A)(this,t);for(var o=arguments.length,r=new Array(o),n=0;n<o;n++)r[n]=arguments[n];return(e=(0,i.A)(this,t,[].concat(r))).disabled=!1,e.required=!0,e}return(0,s.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){return(0,u.qy)(p||(p=f`<ha-addon-picker
      .hass=${0}
      .value=${0}
      .label=${0}
      .helper=${0}
      .disabled=${0}
      .required=${0}
      allow-custom-entity
    ></ha-addon-picker>`),this.hass,this.value,this.label,this.helper,this.disabled,this.required)}}])}(u.WF);_.styles=(0,u.AH)(v||(v=f`
    ha-addon-picker {
      width: 100%;
    }
  `)),(0,d.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,d.__decorate)([(0,c.MZ)({attribute:!1})],_.prototype,"selector",void 0),(0,d.__decorate)([(0,c.MZ)()],_.prototype,"value",void 0),(0,d.__decorate)([(0,c.MZ)()],_.prototype,"label",void 0),(0,d.__decorate)([(0,c.MZ)()],_.prototype,"helper",void 0),(0,d.__decorate)([(0,c.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,d.__decorate)([(0,c.MZ)({type:Boolean})],_.prototype,"required",void 0),_=(0,d.__decorate)([(0,c.EM)("ha-selector-addon")],_),r()}catch(y){r(y)}}))},34402:function(e,t,o){o.d(t,{xG:function(){return u},b3:function(){return s},eK:function(){return d}});var r=o(61397),a=o(50264),n=(o(16280),o(50113),o(18111),o(20116),o(26099),o(53045)),i=o(95260),s=function(){var e=(0,a.A)((0,r.A)().m((function e(t){var o;return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:if(!(0,n.v)(t.config.version,2021,2,4)){e.n=1;break}return e.a(2,t.callWS({type:"supervisor/api",endpoint:"/addons",method:"get"}));case 1:return o=i.PS,e.n=2,t.callApi("GET","hassio/addons");case 2:return e.a(2,o(e.v))}}),e)})));return function(t){return e.apply(this,arguments)}}(),d=function(){var e=(0,a.A)((0,r.A)().m((function e(t,o){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:if(!(0,n.v)(t.config.version,2021,2,4)){e.n=1;break}return e.a(2,t.callWS({type:"supervisor/api",endpoint:`/addons/${o}/start`,method:"post",timeout:null}));case 1:return e.a(2,t.callApi("POST",`hassio/addons/${o}/start`))}}),e)})));return function(t,o){return e.apply(this,arguments)}}(),u=function(){var e=(0,a.A)((0,r.A)().m((function e(t,o){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:if(!(0,n.v)(t.config.version,2021,2,4)){e.n=2;break}return e.n=1,t.callWS({type:"supervisor/api",endpoint:`/addons/${o}/install`,method:"post",timeout:null});case 1:case 3:return e.a(2);case 2:return e.n=3,t.callApi("POST",`hassio/addons/${o}/install`)}}),e)})));return function(t,o){return e.apply(this,arguments)}}()},95260:function(e,t,o){o.d(t,{PS:function(){return r},VR:function(){return a}});o(61397),o(50264),o(74423),o(23792),o(26099),o(31415),o(17642),o(58004),o(33853),o(45876),o(32475),o(15024),o(31698),o(62953),o(53045);var r=e=>e.data,a=e=>"object"==typeof e?"object"==typeof e.body?e.body.message||"Unknown error, see supervisor logs":e.body||e.message||"Unknown error, see supervisor logs":e;new Set([502,503,504])}}]);
//# sourceMappingURL=4924.55fa14975ca54d6f.js.map