"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["8550"],{29989:function(e,a,t){t.r(a),t.d(a,{HaFormExpandable:function(){return _}});var o,i,n,c,r,s=t(94741),l=t(44734),d=t(56038),h=t(69683),p=t(6454),u=(t(28706),t(26099),t(38781),t(62826)),m=t(96196),v=t(77845),b=(t(91120),t(34811),e=>e),_=function(e){function a(){var e;(0,l.A)(this,a);for(var t=arguments.length,o=new Array(t),i=0;i<t;i++)o[i]=arguments[i];return(e=(0,h.A)(this,a,[].concat(o))).disabled=!1,e._computeLabel=(a,t,o)=>e.computeLabel?e.computeLabel(a,t,Object.assign(Object.assign({},o),{},{path:[].concat((0,s.A)((null==o?void 0:o.path)||[]),[e.schema.name])})):e.computeLabel,e._computeHelper=(a,t)=>e.computeHelper?e.computeHelper(a,Object.assign(Object.assign({},t),{},{path:[].concat((0,s.A)((null==t?void 0:t.path)||[]),[e.schema.name])})):e.computeHelper,e}return(0,p.A)(a,e),(0,d.A)(a,[{key:"_renderDescription",value:function(){var e,a=null===(e=this.computeHelper)||void 0===e?void 0:e.call(this,this.schema);return a?(0,m.qy)(o||(o=b`<p>${0}</p>`),a):m.s6}},{key:"render",value:function(){var e,a,t;return(0,m.qy)(i||(i=b`
      <ha-expansion-panel outlined .expanded=${0}>
        ${0}
        <div
          slot="header"
          role="heading"
          aria-level=${0}
        >
          ${0}
        </div>
        <div class="content">
          ${0}
          <ha-form
            .hass=${0}
            .data=${0}
            .schema=${0}
            .disabled=${0}
            .computeLabel=${0}
            .computeHelper=${0}
            .localizeValue=${0}
          ></ha-form>
        </div>
      </ha-expansion-panel>
    `),Boolean(this.schema.expanded),this.schema.icon?(0,m.qy)(n||(n=b`
              <ha-icon slot="leading-icon" .icon=${0}></ha-icon>
            `),this.schema.icon):this.schema.iconPath?(0,m.qy)(c||(c=b`
                <ha-svg-icon
                  slot="leading-icon"
                  .path=${0}
                ></ha-svg-icon>
              `),this.schema.iconPath):m.s6,null!==(e=null===(a=this.schema.headingLevel)||void 0===a?void 0:a.toString())&&void 0!==e?e:"3",this.schema.title||(null===(t=this.computeLabel)||void 0===t?void 0:t.call(this,this.schema)),this._renderDescription(),this.hass,this.data,this.schema.schema,this.disabled,this._computeLabel,this._computeHelper,this.localizeValue)}}])}(m.WF);_.styles=(0,m.AH)(r||(r=b`
    :host {
      display: flex !important;
      flex-direction: column;
    }
    :host ha-form {
      display: block;
    }
    .content {
      padding: 12px;
    }
    .content p {
      margin: 0 0 24px;
    }
    ha-expansion-panel {
      display: block;
      --expansion-panel-content-padding: 0;
      border-radius: var(--ha-border-radius-md);
      --ha-card-border-radius: var(--ha-border-radius-md);
    }
    ha-svg-icon,
    ha-icon {
      color: var(--secondary-text-color);
    }
  `)),(0,u.__decorate)([(0,v.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,u.__decorate)([(0,v.MZ)({attribute:!1})],_.prototype,"data",void 0),(0,u.__decorate)([(0,v.MZ)({attribute:!1})],_.prototype,"schema",void 0),(0,u.__decorate)([(0,v.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,u.__decorate)([(0,v.MZ)({attribute:!1})],_.prototype,"computeLabel",void 0),(0,u.__decorate)([(0,v.MZ)({attribute:!1})],_.prototype,"computeHelper",void 0),(0,u.__decorate)([(0,v.MZ)({attribute:!1})],_.prototype,"localizeValue",void 0),_=(0,u.__decorate)([(0,v.EM)("ha-form-expandable")],_)}}]);
//# sourceMappingURL=8550.157084cb42d320c4.js.map