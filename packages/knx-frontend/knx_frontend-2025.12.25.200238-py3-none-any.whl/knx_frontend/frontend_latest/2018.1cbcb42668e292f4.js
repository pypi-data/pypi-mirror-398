export const __webpack_id__="2018";export const __webpack_ids__=["2018"];export const __webpack_modules__={49337:function(e,o,t){t.r(o),t.d(o,{HaFormBoolean:()=>s});var a=t(62826),r=t(96196),i=t(77845),d=t(92542);t(70524),t(48543);class s extends r.WF{focus(){this._input&&this._input.focus()}render(){return r.qy`
      <ha-formfield .label=${this.label}>
        <ha-checkbox
          .checked=${this.data}
          .disabled=${this.disabled}
          @change=${this._valueChanged}
        ></ha-checkbox>
        <span slot="label">
          <p class="primary">${this.label}</p>
          ${this.helper?r.qy`<p class="secondary">${this.helper}</p>`:r.s6}
        </span>
      </ha-formfield>
    `}_valueChanged(e){(0,d.r)(this,"value-changed",{value:e.target.checked})}constructor(...e){super(...e),this.disabled=!1}}s.styles=r.AH`
    ha-formfield {
      display: flex;
      min-height: 56px;
      align-items: center;
      --mdc-typography-body2-font-size: 1em;
    }
    p {
      margin: 0;
    }
    .secondary {
      direction: var(--direction);
      padding-top: 4px;
      box-sizing: border-box;
      color: var(--secondary-text-color);
      font-size: 0.875rem;
      font-weight: var(
        --mdc-typography-body2-font-weight,
        var(--ha-font-weight-normal)
      );
    }
  `,(0,a.__decorate)([(0,i.MZ)({attribute:!1})],s.prototype,"schema",void 0),(0,a.__decorate)([(0,i.MZ)({attribute:!1})],s.prototype,"data",void 0),(0,a.__decorate)([(0,i.MZ)()],s.prototype,"label",void 0),(0,a.__decorate)([(0,i.MZ)()],s.prototype,"helper",void 0),(0,a.__decorate)([(0,i.MZ)({type:Boolean})],s.prototype,"disabled",void 0),(0,a.__decorate)([(0,i.P)("ha-checkbox",!0)],s.prototype,"_input",void 0),s=(0,a.__decorate)([(0,i.EM)("ha-form-boolean")],s)}};
//# sourceMappingURL=2018.1cbcb42668e292f4.js.map