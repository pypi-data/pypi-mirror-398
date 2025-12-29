<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:jp="http://www.jpo.go.jp"
  exclude-result-prefixes="jp">

  <xsl:output method="html" encoding="utf-8" omit-xml-declaration="yes" indent="yes"
    media-type="text/html" />

  <xsl:include href="parts/v4xva_ntc-pt-e.xsl" />

  <!-- lookup table defined in source xml. -->
  <xsl:key name="procedure-params" match="procedure-param" use="@name" />

  <xsl:template match="/root">
    <xsl:element name="div">
      <xsl:apply-templates select="jp:cpy-notice-pat-exam" />
    </xsl:element>
  </xsl:template>

  <!-- ====================================================================
     jp:cpy-notice-pat-exam
     ====================================================================-->
  <xsl:template match="jp:cpy-notice-pat-exam">
    <xsl:apply-templates select="jp:dispatch-control-article" />
    <xsl:apply-templates select="jp:notice-pat-exam" />
  </xsl:template>

</xsl:stylesheet>