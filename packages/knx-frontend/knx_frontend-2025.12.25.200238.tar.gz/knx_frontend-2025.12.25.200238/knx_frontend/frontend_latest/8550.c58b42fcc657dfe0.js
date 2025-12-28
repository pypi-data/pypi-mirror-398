export const __webpack_id__="8550";export const __webpack_ids__=["8550"];export const __webpack_modules__={29989:function(e,t,a){a.r(t),a.d(t,{HaFormExpandable:()=>c});var o=a(62826),i=a(96196),s=a(77845);a(91120),a(34811);class c extends i.WF{_renderDescription(){const e=this.computeHelper?.(this.schema);return e?i.qy`<p>${e}</p>`:i.s6}render(){return i.qy`
      <ha-expansion-panel outlined .expanded=${Boolean(this.schema.expanded)}>
        ${this.schema.icon?i.qy`
              <ha-icon slot="leading-icon" .icon=${this.schema.icon}></ha-icon>
            `:this.schema.iconPath?i.qy`
                <ha-svg-icon
                  slot="leading-icon"
                  .path=${this.schema.iconPath}
                ></ha-svg-icon>
              `:i.s6}
        <div
          slot="header"
          role="heading"
          aria-level=${this.schema.headingLevel?.toString()??"3"}
        >
          ${this.schema.title||this.computeLabel?.(this.schema)}
        </div>
        <div class="content">
          ${this._renderDescription()}
          <ha-form
            .hass=${this.hass}
            .data=${this.data}
            .schema=${this.schema.schema}
            .disabled=${this.disabled}
            .computeLabel=${this._computeLabel}
            .computeHelper=${this._computeHelper}
            .localizeValue=${this.localizeValue}
          ></ha-form>
        </div>
      </ha-expansion-panel>
    `}constructor(...e){super(...e),this.disabled=!1,this._computeLabel=(e,t,a)=>this.computeLabel?this.computeLabel(e,t,{...a,path:[...a?.path||[],this.schema.name]}):this.computeLabel,this._computeHelper=(e,t)=>this.computeHelper?this.computeHelper(e,{...t,path:[...t?.path||[],this.schema.name]}):this.computeHelper}}c.styles=i.AH`
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
  `,(0,o.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"hass",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"data",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"schema",void 0),(0,o.__decorate)([(0,s.MZ)({type:Boolean})],c.prototype,"disabled",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"computeLabel",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"computeHelper",void 0),(0,o.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"localizeValue",void 0),c=(0,o.__decorate)([(0,s.EM)("ha-form-expandable")],c)}};
//# sourceMappingURL=8550.c58b42fcc657dfe0.js.map