import{bP as y,d as u,n as L,q as l,K as k,L as w,a0 as c,M as i,a1 as x,S as B,A as S,R as M}from"./index-Ci_yf8On.js";function $(e,o,r){var a=-1,n=e.length;o<0&&(o=-o>n?0:n+o),r=r>n?n:r,r<0&&(r+=n),n=o>r?0:r-o>>>0,o>>>=0;for(var s=Array(n);++a<n;)s[a]=e[a+o];return s}function z(e,o,r){var a=e.length;return r=r===void 0?a:r,!o&&r>=a?e:$(e,o,r)}var A="\\ud800-\\udfff",P="\\u0300-\\u036f",T="\\ufe20-\\ufe2f",j="\\u20d0-\\u20ff",I=P+T+j,N="\\ufe0e\\ufe0f",F="\\u200d",O=RegExp("["+F+A+I+N+"]");function b(e){return O.test(e)}function U(e){return e.split("")}var v="\\ud800-\\udfff",q="\\u0300-\\u036f",E="\\ufe20-\\ufe2f",H="\\u20d0-\\u20ff",J=q+E+H,V="\\ufe0e\\ufe0f",Z="["+v+"]",d="["+J+"]",f="\\ud83c[\\udffb-\\udfff]",K="(?:"+d+"|"+f+")",g="[^"+v+"]",h="(?:\\ud83c[\\udde6-\\uddff]){2}",p="[\\ud800-\\udbff][\\udc00-\\udfff]",W="\\u200d",C=K+"?",m="["+V+"]?",_="(?:"+W+"(?:"+[g,h,p].join("|")+")"+m+C+")*",D=m+C+_,X="(?:"+[g+d+"?",d,h,p,Z].join("|")+")",Y=RegExp(f+"(?="+f+")|"+X+D,"g");function G(e){return e.match(Y)||[]}function Q(e){return b(e)?G(e):U(e)}function ee(e){return function(o){o=y(o);var r=b(o)?Q(o):void 0,a=r?r[0]:o.charAt(0),n=r?z(r,1).join(""):o.slice(1);return a[e]()+n}}var oe=ee("toUpperCase");function re(e,o){const r=u({render(){return o()}});return u({name:oe(e),setup(){var a;const n=(a=L(k,null))===null||a===void 0?void 0:a.mergedIconsRef;return()=>{var s;const t=(s=n?.value)===null||s===void 0?void 0:s[e];return t?t():l(r,null)}}})}const ne=re("close",()=>l("svg",{viewBox:"0 0 12 12",version:"1.1",xmlns:"http://www.w3.org/2000/svg","aria-hidden":!0},l("g",{stroke:"none","stroke-width":"1",fill:"none","fill-rule":"evenodd"},l("g",{fill:"currentColor","fill-rule":"nonzero"},l("path",{d:"M2.08859116,2.2156945 L2.14644661,2.14644661 C2.32001296,1.97288026 2.58943736,1.95359511 2.7843055,2.08859116 L2.85355339,2.14644661 L6,5.293 L9.14644661,2.14644661 C9.34170876,1.95118446 9.65829124,1.95118446 9.85355339,2.14644661 C10.0488155,2.34170876 10.0488155,2.65829124 9.85355339,2.85355339 L6.707,6 L9.85355339,9.14644661 C10.0271197,9.32001296 10.0464049,9.58943736 9.91140884,9.7843055 L9.85355339,9.85355339 C9.67998704,10.0271197 9.41056264,10.0464049 9.2156945,9.91140884 L9.14644661,9.85355339 L6,6.707 L2.85355339,9.85355339 C2.65829124,10.0488155 2.34170876,10.0488155 2.14644661,9.85355339 C1.95118446,9.65829124 1.95118446,9.34170876 2.14644661,9.14644661 L5.293,6 L2.14644661,2.85355339 C1.97288026,2.67998704 1.95359511,2.41056264 2.08859116,2.2156945 L2.14644661,2.14644661 L2.08859116,2.2156945 Z"}))))),ae=w("base-close",`
 display: flex;
 align-items: center;
 justify-content: center;
 cursor: pointer;
 background-color: transparent;
 color: var(--n-close-icon-color);
 border-radius: var(--n-close-border-radius);
 height: var(--n-close-size);
 width: var(--n-close-size);
 font-size: var(--n-close-icon-size);
 outline: none;
 border: none;
 position: relative;
 padding: 0;
`,[c("absolute",`
 height: var(--n-close-icon-size);
 width: var(--n-close-icon-size);
 `),i("&::before",`
 content: "";
 position: absolute;
 width: var(--n-close-size);
 height: var(--n-close-size);
 left: 50%;
 top: 50%;
 transform: translateY(-50%) translateX(-50%);
 transition: inherit;
 border-radius: inherit;
 `),x("disabled",[i("&:hover",`
 color: var(--n-close-icon-color-hover);
 `),i("&:hover::before",`
 background-color: var(--n-close-color-hover);
 `),i("&:focus::before",`
 background-color: var(--n-close-color-hover);
 `),i("&:active",`
 color: var(--n-close-icon-color-pressed);
 `),i("&:active::before",`
 background-color: var(--n-close-color-pressed);
 `)]),c("disabled",`
 cursor: not-allowed;
 color: var(--n-close-icon-color-disabled);
 background-color: transparent;
 `),c("round",[i("&::before",`
 border-radius: 50%;
 `)])]),le=u({name:"BaseClose",props:{isButtonTag:{type:Boolean,default:!0},clsPrefix:{type:String,required:!0},disabled:{type:Boolean,default:void 0},focusable:{type:Boolean,default:!0},round:Boolean,onClick:Function,absolute:Boolean},setup(e){return B("-base-close",ae,S(e,"clsPrefix")),()=>{const{clsPrefix:o,disabled:r,absolute:a,round:n,isButtonTag:s}=e;return l(s?"button":"div",{type:s?"button":void 0,tabindex:r||!e.focusable?-1:0,"aria-disabled":r,"aria-label":"close",role:s?void 0:"button",disabled:r,class:[`${o}-base-close`,a&&`${o}-base-close--absolute`,r&&`${o}-base-close--disabled`,n&&`${o}-base-close--round`],onMousedown:R=>{e.focusable||R.preventDefault()},onClick:e.onClick},l(M,{clsPrefix:o},{default:()=>l(ne,null)}))}}});export{le as N,re as r};
