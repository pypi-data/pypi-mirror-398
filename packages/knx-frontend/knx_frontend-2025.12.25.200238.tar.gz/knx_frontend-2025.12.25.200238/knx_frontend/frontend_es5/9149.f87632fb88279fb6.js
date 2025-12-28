"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["9149"],{40783:function(e,t,s){s.d(t,{H:function(){return i}});var i=(e,t,s,i,r)=>e.connection.subscribeMessage(r,{type:"template/start_preview",flow_id:t,flow_type:s,user_input:i})},71996:function(e,t,s){s.a(e,(async function(e,i){try{s.r(t);var r=s(61397),a=s(50264),n=s(44734),o=s(56038),l=s(69683),_=s(6454),u=s(25460),p=(s(28706),s(62062),s(26910),s(18111),s(61701),s(26099),s(62826)),h=s(96196),c=s(77845),d=s(40404),v=s(40783),w=s(2103),b=s(92542),f=(s(17963),e([w]));w=(f.then?(await f)():f)[0];var y,g,m,k,$,A,q,M,z=e=>e,P=function(e){function t(){var e;(0,n.A)(this,t);for(var s=arguments.length,i=new Array(s),r=0;r<s;r++)i[r]=arguments[r];return(e=(0,l.A)(this,t,[].concat(i)))._setPreview=t=>{if("error"in t)return e._error=t.error,void(e._preview=void 0);e._error=void 0,e._listeners=t.listeners;var s=(new Date).toISOString();e._preview={entity_id:`${e.stepId}.___flow_preview___`,last_changed:s,last_updated:s,context:{id:"",parent_id:null,user_id:null},attributes:t.attributes,state:t.state}},e._debouncedSubscribePreview=(0,d.s)((()=>{e._subscribePreview()}),250),e}return(0,_.A)(t,e),(0,o.A)(t,[{key:"disconnectedCallback",value:function(){(0,u.A)(t,"disconnectedCallback",this,3)([]),this._unsub&&(this._unsub.then((e=>e())),this._unsub=void 0)}},{key:"willUpdate",value:function(e){e.has("stepData")&&this._debouncedSubscribePreview()}},{key:"render",value:function(){var e;return this._error?(0,h.qy)(y||(y=z`<ha-alert alert-type="error">${0}</ha-alert>`),this._error):(0,h.qy)(g||(g=z`<entity-preview-row
        .hass=${0}
        .stateObj=${0}
      ></entity-preview-row>
      ${0}
      ${0} `),this.hass,this._preview,null!==(e=this._listeners)&&void 0!==e&&e.time?(0,h.qy)(m||(m=z`
            <p>
              ${0}
            </p>
          `),this.hass.localize("ui.dialogs.helper_settings.template.time")):h.s6,this._listeners?this._listeners.all?(0,h.qy)(k||(k=z`
              <p class="all_listeners">
                ${0}
              </p>
            `),this.hass.localize("ui.dialogs.helper_settings.template.all_listeners")):this._listeners.domains.length||this._listeners.entities.length?(0,h.qy)($||($=z`
                <p>
                  ${0}
                </p>
                <ul>
                  ${0}
                  ${0}
                </ul>
              `),this.hass.localize("ui.dialogs.helper_settings.template.listeners"),this._listeners.domains.sort().map((e=>(0,h.qy)(A||(A=z`
                        <li>
                          <b
                            >${0}</b
                          >: ${0}
                        </li>
                      `),this.hass.localize("ui.dialogs.helper_settings.template.domain"),e))),this._listeners.entities.sort().map((e=>(0,h.qy)(q||(q=z`
                        <li>
                          <b
                            >${0}</b
                          >: ${0}
                        </li>
                      `),this.hass.localize("ui.dialogs.helper_settings.template.entity"),e)))):this._listeners.time?h.s6:(0,h.qy)(M||(M=z`<p class="all_listeners">
                  ${0}
                </p>`),this.hass.localize("ui.dialogs.helper_settings.template.no_listeners")):h.s6)}},{key:"_subscribePreview",value:(s=(0,a.A)((0,r.A)().m((function e(){var t;return(0,r.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(!this._unsub){e.n=2;break}return e.n=1,this._unsub;case 1:(0,e.v)(),this._unsub=void 0;case 2:if("config_flow"===this.flowType||"options_flow"===this.flowType){e.n=3;break}return e.a(2);case 3:return e.p=3,this._unsub=(0,v.H)(this.hass,this.flowId,this.flowType,this.stepData,this._setPreview),e.n=4,this._unsub;case 4:(0,b.r)(this,"set-flow-errors",{errors:{}}),e.n=6;break;case 5:e.p=5,"string"==typeof(t=e.v).message?this._error=t.message:(this._error=void 0,(0,b.r)(this,"set-flow-errors",t.message)),this._unsub=void 0,this._preview=void 0;case 6:return e.a(2)}}),e,this,[[3,5]])}))),function(){return s.apply(this,arguments)})}]);var s}(h.WF);(0,p.__decorate)([(0,c.MZ)({attribute:!1})],P.prototype,"hass",void 0),(0,p.__decorate)([(0,c.MZ)({attribute:!1})],P.prototype,"flowType",void 0),(0,p.__decorate)([(0,c.MZ)({attribute:!1})],P.prototype,"stepId",void 0),(0,p.__decorate)([(0,c.MZ)({attribute:!1})],P.prototype,"flowId",void 0),(0,p.__decorate)([(0,c.MZ)({attribute:!1})],P.prototype,"stepData",void 0),(0,p.__decorate)([(0,c.wk)()],P.prototype,"_preview",void 0),(0,p.__decorate)([(0,c.wk)()],P.prototype,"_listeners",void 0),(0,p.__decorate)([(0,c.wk)()],P.prototype,"_error",void 0),P=(0,p.__decorate)([(0,c.EM)("flow-preview-template")],P),i()}catch(I){i(I)}}))}}]);
//# sourceMappingURL=9149.f87632fb88279fb6.js.map