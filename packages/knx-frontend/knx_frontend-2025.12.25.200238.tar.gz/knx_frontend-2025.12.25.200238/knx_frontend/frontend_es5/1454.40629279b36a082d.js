"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["1454"],{2173:function(t,e,a){a.a(t,(async function(t,i){try{a.r(e),a.d(e,{HaFormOptionalActions:function(){return V}});var o=a(94741),s=a(61397),n=a(50264),c=a(44734),l=a(56038),r=a(69683),d=a(6454),h=a(25460),u=(a(28706),a(2008),a(74423),a(23792),a(62062),a(18111),a(22489),a(61701),a(36033),a(26099),a(62953),a(62826)),p=a(96196),m=a(77845),_=a(22786),y=a(55124),v=a(89473),f=(a(56565),a(60961),a(91120),t([v]));v=(f.then?(await f)():f)[0];var A,b,$,k,H,M=t=>t,g=[],V=function(t){function e(){var t;(0,c.A)(this,e);for(var a=arguments.length,i=new Array(a),o=0;o<a;o++)i[o]=arguments[o];return(t=(0,r.A)(this,e,[].concat(i))).disabled=!1,t._hiddenActions=(0,_.A)(((t,e)=>t.map((t=>t.name)).filter((t=>!e.includes(t))))),t._displaySchema=(0,_.A)(((t,e)=>t.filter((t=>e.includes(t.name))))),t}return(0,d.A)(e,t),(0,l.A)(e,[{key:"focus",value:(a=(0,n.A)((0,s.A)().m((function t(){var e;return(0,s.A)().w((function(t){for(;;)switch(t.n){case 0:return t.n=1,this.updateComplete;case 1:null===(e=this.renderRoot.querySelector("ha-form"))||void 0===e||e.focus();case 2:return t.a(2)}}),t,this)}))),function(){return a.apply(this,arguments)})},{key:"updated",value:function(t){if((0,h.A)(e,"updated",this,3)([t]),t.has("data")){var a,i=null!==(a=this._displayActions)&&void 0!==a?a:g,s=this._hiddenActions(this.schema.schema,i);this._displayActions=[].concat((0,o.A)(i),(0,o.A)(s.filter((t=>t in this.data))))}}},{key:"render",value:function(){var t,e,a,i=null!==(t=this._displayActions)&&void 0!==t?t:g,o=this._displaySchema(this.schema.schema,null!==(e=this._displayActions)&&void 0!==e?e:[]),s=this._hiddenActions(this.schema.schema,i),n=new Map(this.computeLabel?this.schema.schema.map((t=>[t.name,t])):[]);return(0,p.qy)(A||(A=M`
      ${0}
      ${0}
    `),o.length>0?(0,p.qy)(b||(b=M`
            <ha-form
              .hass=${0}
              .data=${0}
              .schema=${0}
              .disabled=${0}
              .computeLabel=${0}
              .computeHelper=${0}
              .localizeValue=${0}
            ></ha-form>
          `),this.hass,this.data,o,this.disabled,this.computeLabel,this.computeHelper,this.localizeValue):p.s6,s.length>0?(0,p.qy)($||($=M`
            <ha-button-menu
              @action=${0}
              fixed
              @closed=${0}
            >
              <ha-button slot="trigger" appearance="filled" size="small">
                <ha-svg-icon .path=${0} slot="start"></ha-svg-icon>
                ${0}
              </ha-button>
              ${0}
            </ha-button-menu>
          `),this._handleAddAction,y.d,"M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",(null===(a=this.localize)||void 0===a?void 0:a.call(this,"ui.components.form-optional-actions.add"))||"Add interaction",s.map((t=>{var e=n.get(t);return(0,p.qy)(k||(k=M`
                  <ha-list-item>
                    ${0}
                  </ha-list-item>
                `),this.computeLabel&&e?this.computeLabel(e):t)}))):p.s6)}},{key:"_handleAddAction",value:function(t){var e,a,i=this._hiddenActions(this.schema.schema,null!==(e=this._displayActions)&&void 0!==e?e:g)[t.detail.index];this._displayActions=[].concat((0,o.A)(null!==(a=this._displayActions)&&void 0!==a?a:[]),[i])}}]);var a}(p.WF);V.styles=(0,p.AH)(H||(H=M`
    :host {
      display: flex !important;
      flex-direction: column;
      gap: var(--ha-space-6);
    }
    :host ha-form {
      display: block;
    }
  `)),(0,u.__decorate)([(0,m.MZ)({attribute:!1})],V.prototype,"localize",void 0),(0,u.__decorate)([(0,m.MZ)({attribute:!1})],V.prototype,"hass",void 0),(0,u.__decorate)([(0,m.MZ)({attribute:!1})],V.prototype,"data",void 0),(0,u.__decorate)([(0,m.MZ)({attribute:!1})],V.prototype,"schema",void 0),(0,u.__decorate)([(0,m.MZ)({type:Boolean})],V.prototype,"disabled",void 0),(0,u.__decorate)([(0,m.MZ)({attribute:!1})],V.prototype,"computeLabel",void 0),(0,u.__decorate)([(0,m.MZ)({attribute:!1})],V.prototype,"computeHelper",void 0),(0,u.__decorate)([(0,m.MZ)({attribute:!1})],V.prototype,"localizeValue",void 0),(0,u.__decorate)([(0,m.wk)()],V.prototype,"_displayActions",void 0),V=(0,u.__decorate)([(0,m.EM)("ha-form-optional_actions")],V),i()}catch(Z){i(Z)}}))}}]);
//# sourceMappingURL=1454.40629279b36a082d.js.map