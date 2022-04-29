# Sample Materials, provided under license.
# Licensed Materials - Property of IBM
# © Copyright IBM Corp. 2020, 2021. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by GSA ADP Schedule Contract with IBM Corp.



clientPanel <- function() {
  
  tabPanel(
    "Client View",
    value = "clientPanel",
    shinyjs::useShinyjs(),
    shinyjs::extendShinyjs(text = refreshCode, functions = c("refresh")),
    
    panel(
      br(),br(),
      fluidRow(
        column(3, class = "pull-left",
               div(id = "customerImage"),
               h2(class = "text-center" ,textOutput("customerName"))),
        column(4, 
               h4("Personal Information", class="text-center"),
               hr(),
               uiOutput("customerInfo")
        ),
        column(4, class = "pull-right", 
               h4("Financial Profile", class="text-center"),
               hr(),
               uiOutput("customerFinancesInfo")
        )
      ),
      br()
    ),
    
    panel(
      h3("Account Details"),
      br(),
      column(12, offset = 1, tableOutput("customerAccountsTable")),
      br(),
      column(12, offset = 1,tableOutput("customerAccountSummaryTable"))
    ),
    
    panel(
      h3("Attrition Prediction "),
      br(),
      

      
      tags$div(
        id = "authPanel",
        column(4,
          panel(
            h4("Connect to IBM Cloud API"),
            # textInput("hostname", "Hostname"),
            #textInput("username", "REGION (e.g: us-south)"),
            #tags$h4("Select Region"),
            pickerInput(
              inputId = 'username',
              label = 'Select a Region',
              choices = list("us-south","eu-de","eu-gb","jp_tok"),
              options = pickerOptions(width = "auto", style = "btn-primary")
            ),
            passwordInput("password", "API KEY"),
            actionButton("authBtn", "Authenticate API", class = "btn-primary btn-lg btn-block", style = "max-width:300px", disabled = TRUE),
            tags$head(tags$style("#authError{color:red;}")),
            verbatimTextOutput("authError")
          ),
          style = "max-width:360px;"
        )
      ),
      hidden(
        tags$div(
          id = "deploymentPanel",
          column(4,
             panel(
               tags$h4("Model Scoring Pipeline Deployment"),
               pickerInput(
                 inputId = 'deploymentSelector',
                 label = 'Deployment:',
                 choices = list(),
                 options = pickerOptions(width = "auto", style = "btn-primary")
               ),
               tags$p(
                 tags$strong("Space Name: "),
                 textOutput(outputId = "space_name", inline = TRUE)
               ),
               tags$p(
                 tags$strong("GUID: "),
                 textOutput(outputId = "deployment_guid", inline = TRUE)
               ),
               #tags$p(
               #  tags$strong("Tags: "),
               #  textOutput(outputId = "deployment_tags", inline = TRUE),
               #  style = "word-wrap: break-word"
               #),
               tags$p(
                 tags$strong("Scoring Endpoint: "),
                 textOutput(outputId = "scoring_url", inline = TRUE),
                 style = "word-wrap: break-word"
               )
             ),
             panel(actionButton("refresh", "Back to Home", class = "btn-primary btn-sm btn-block"))
             
          ),
          tags$div(id = "scoreBtnSection",
            column(4,
              br(),br(),
              actionButton(
                 "scoreBtn",
                 "Predict Attrition",
                 class = "btn-primary btn-lg btn-block",
                 disabled = TRUE
               ),
              br(),
              h4("Input JSON:"),
              verbatimTextOutput("pipelineInput"),
              br(),
              tags$head(tags$style("#scoringError{color:red;}")),
              verbatimTextOutput("scoringError"))
          ),
          column(8,
             hidden(
               tags$div(id = "scoringResponse")
             )
          )
        )
      )
    )
  )
}

# Reactive server variables store (pervades across all sessions)
serverVariables = reactiveValues(deployments = list(), token = '')

if(nchar(Sys.getenv('CP4D_HOSTNAME')) > 0 && nchar(Sys.getenv('CP4D_USERNAME')) > 0 && nchar(Sys.getenv('CP4D_PASSWORD')) > 0) {
  tryCatch({
    deploymentsResp = collectDeployments(input$username, input$password, "Customer-Attrition-Prediction-Scoring-Function-Deployment")
    serverVariables$deployments <- deploymentsResp$deployments
    serverVariables$token = deploymentsResp$token
  }, warning = function(w) {
    print(w$message)
  }, error = function(e) {
    print(e$message)
  })
}
refreshCode <- "shinyjs.refresh = function() { location.reload(); }"
clientServer <- function(input, output, session, sessionVars) {
  #refresh page
  observeEvent( input$refresh, {shinyjs::js$refresh()})
  observe({

    client <- clients[[toString(sessionVars$selectedClientId)]]

    # Update client name & image
    output$customerName <- renderText(client$name)
    removeUI(selector = "#customerImage > *")
    insertUI(
      selector = "#customerImage",
      where = "beforeEnd",
      ui = img(src = paste0("profiles/",client$image), style = "display: block;margin-left: auto;margin-right: auto;", width=150, height=150)
    )
    
    # Load customer data for customer sessionVars$selectedClientId
    selection <- customer[customer$CUSTOMER_ID == sessionVars$selectedClientId,][1,]
    

    
    output$customerInfo <- renderUI({
      infoDets <- selection[,c("AGE_RANGE", "MARITAL_STATUS", "FAMILY_SIZE", "PROFESSION", "EDUCATION_LEVEL")]
      infoDets[["FAMILY_SIZE"]] <- as.integer(infoDets[["FAMILY_SIZE"]])
      infoDets[["ADDRESS"]] <- paste(selection[,"ADDRESS_HOME_CITY"], selection[,"ADDRESS_HOME_STATE"], sep = ', ')
      tags$ul( class = 'list-unstyled',
               tags$li(
                 tags$strong('Age: '), tags$span(class = "pull-right", infoDets[["AGE_RANGE"]], ' years old')
               ),
               tags$li(
                 tags$strong('Marital Status: '),tags$span(class = "pull-right", infoDets[["MARITAL_STATUS"]])
               ),
               tags$li(
                 tags$strong('Address: '), tags$span(class = "pull-right", infoDets[["ADDRESS"]])
               ),
               tags$li(
                 tags$strong('Profession: '), tags$span(class = "pull-right",infoDets[["PROFESSION"]])
               ),
               tags$li(
                 tags$strong('Level of Education: '), tags$span(class = "pull-right", infoDets[["EDUCATION_LEVEL"]])
               )
      )
    })
    
    

    
    output$customerFinancesInfo <- renderUI({
      customerfinDets <- selection[,c("ANNUAL_INCOME", "HOME_OWNER_INDICATOR", "MONTHLY_HOUSING_COST", "CREDIT_SCORE", "CREDIT_AUTHORITY_LEVEL")]
      customerfinDets[["ANNUAL_INCOME"]] <- dollar(customerfinDets[["ANNUAL_INCOME"]])
      customerfinDets[["MONTHLY_HOUSING_COST"]] <- dollar(customerfinDets[["MONTHLY_HOUSING_COST"]])
      tags$ul( class = 'list-unstyled',
               tags$li(
                 tags$strong('Annual income: '), tags$span(class="pull-right", customerfinDets[["ANNUAL_INCOME"]])
               ),
               tags$li(
                 tags$strong('Home Owner: '), tags$span(class="pull-right", if(customerfinDets[["HOME_OWNER_INDICATOR"]] == TRUE) { 'Yes'} else { 'No'})
               ),
               tags$li(
                 tags$strong('Monthly Housing: '), tags$span(class="pull-right", customerfinDets[["MONTHLY_HOUSING_COST"]])
               ),
               tags$li(
                 tags$strong('Credit Score: '), tags$span(class="pull-right", round(customerfinDets[["CREDIT_SCORE"]], 0))
               ),
               tags$li(
                 tags$strong('Credit Authority Level: '), tags$span(class="pull-right", customerfinDets[["CREDIT_AUTHORITY_LEVEL"]])
               )
               
      )
    })
    
    customerAccounts <- account[account$PRIMARY_CUSTOMER_ID == sessionVars$selectedClientId,][1,]
    
    output$customerAccountsTable <- renderTable({
      customerAccountsInfo <- customerAccounts[,c("ACCOUNT_ID", "ACCOUNT_TYPE", "PRODUCT_ID", "BASE_CURRENCY", "INVESTMENT_OBJECTIVE", "LIFE_CYCLE_STATUS", "RISK_TOLERANCE", "TAX_ADVANTAGE_INDICATOR")]
      for(name in names(customerAccountsInfo)){
        colnames(customerAccountsInfo)[colnames(customerAccountsInfo)==name] <- str_replace_all(name, '_',' ')
      }
      customerAccountsInfo
      },
      bordered = FALSE, align = 'l')
    
    customerAccountSummaries <- account_summary[account_summary$ACCOUNT_ID %in% customerAccounts$ACCOUNT_ID,][1,]
    
    output$customerAccountSummaryTable <- renderTable({
      accountDeets <- customerAccountSummaries[,c("CLOSING_BALANCE", "AMOUNT_OF_DEPOSITS", "AMOUNT_OF_INTEREST_EARNED", "NUMBER_OF_BUY_TRADES", "AMOUNT_OF_BUY_TRADES", "AMOUNT_OF_MARKET_CHANGE")] %>%
        mutate_at(vars(contains("AMOUNT_")), dollar) %>%
        mutate_at(vars(contains("_BALANCE")), dollar) %>%
        mutate_at(vars(contains("NUMBER_")), as.integer)
      for(name in names(accountDeets)){
        colnames(accountDeets)[colnames(accountDeets)==name] <- str_replace_all(name, '_',' ')
      }
      accountDeets
    }, bordered = FALSE, align = 'l')
    
    # Reset scoring
    removeUI(selector = "#scoringResponse > *", multiple = TRUE)
    shinyjs::hide(id = "scoringResponse")
    shinyjs::show(id = "scoreBtnSection")
    output$scoringError <- renderText('')
    sessionVars$pipelineInput <- list(cust_id = sessionVars$selectedClientId, sc_end_date = '2018-09-30')
    output$pipelineInput <- renderText(toJSON(sessionVars$pipelineInput))
  })
  

  # Enable buttons when inputs are provided

  observe({
    toggleState("authBtn",  nchar(input$username) > 0 && nchar(input$password) > 0)
    toggleState("scoreBtn", nchar(input$endpoint) > 0 && nchar(input$token) > 0 && length(input$allCustomers_rows_selected) > 0)
  })
  
  # Handle CP4D API authentication button
  observeEvent(input$authBtn, {
    shinyjs::disable("authBtn")
    
    tryCatch({
      deploymentsResp = collectDeployments(input$username, input$password, "Customer-Attrition-Prediction-Scoring-Function-Deployment")
      serverVariables$deployments <- deploymentsResp$deployments
      serverVariables$token = deploymentsResp$token
    }, warning = function(w) {
      output$authError <- renderText(w$message)
    }, error = function(e) {
      output$authError <- renderText(e$message)
    })
    
    shinyjs::enable("authBtn")

    if(length(serverVariables$deployments) > 0) {
      updateSelectInput(session, "deploymentSelector", choices = names(serverVariables$deployments))
      shinyjs::hide(id = "authPanel")
      shinyjs::show(id = "deploymentPanel")
    }
  })
  
  # Handle model deployment dropdown switching
  observeEvent(input$deploymentSelector, {
    selectedDeployment <- serverVariables$deployments[[input$deploymentSelector]]
    output$deployment_guid <- renderText(selectedDeployment$guid)
    output$space_name <- renderText(selectedDeployment$space_name)
   
    output$scoring_url <- renderText(selectedDeployment$scoring_url)
    toggleState("scoreBtn", nchar(selectedDeployment$scoring_url) > 0 && nchar(serverVariables$token) > 0)
  })
  
  # Handle model deployment scoring button
  observeEvent(input$scoreBtn, {
    shinyjs::disable("scoreBtn")
    
    selectedDeployment <- serverVariables$deployments[[input$deploymentSelector]]
    

    payload = list(
      fields=list("CUSTOMER_ID","sc_end_date"),
      values = list(list(sessionVars$selectedClientId,'2018-09-30'))
    )
    
    print(payload)
    print(serverVariables$token)
    response <- scoreModelDeployment(selectedDeployment$scoring_url, payload, serverVariables$token)

    if(length(response$error) > 0) {
      output$scoringError <- renderText(toString(response$error))
    }
    else if(length(response$predictions) > 0) {
      shinyjs::hide(id = "scoreBtnSection")
      shinyjs::show(id = "scoringResponse")
      
      result <- response$predictions[[1]]$values$predictions[[1]]
    
      insertUI(
        selector = "#scoringResponse",
        where = "beforeEnd",
        ui = panel(
          h3("Customer Attrition Prediction:"),
          p(
            plotOutput("probPlot", width = "600px", height = "300px")
          )
          # explain_panel
        )
      )
      
      
      # generate probability pie
      probDF <- data.frame(t(data.frame(result$values[[1]][[2]])))
      colnames(probDF) <- "Probability"
      row.names(probDF) <- c("FALSE", "TRUE")
      probDF <- tibble::rownames_to_column(probDF, "Prediction")
      probDF <- probDF %>%
        mutate(percentage = paste0(round(100 * Probability, 1), "%")) %>%
        mutate(hover_text = paste0(Prediction, ": ", percentage))
      
      probPlot <- ggplot(probDF, aes(y = Probability, fill = Prediction)) +
        geom_bar(
          aes(x = 1),
          width = 0.4,
          stat = "identity",
          show.legend = TRUE
        ) + 
        annotate("text", x = 0, y = 0, size = 12,
                 label = probDF[["percentage"]][probDF[["Prediction"]] == "TRUE"]
                ) +
        coord_polar(theta = "y") +
        theme_void() +
        theme(legend.title=element_text(size=22),
              legend.text=element_text(size=16)) +
        guides(fill = guide_legend(reverse=TRUE))
      
      output$probPlot <- renderPlot(probPlot, width="auto", height="auto")
      
    } else {
      output$scoringError <- renderText(response)
    }
    
    shinyjs::enable("scoreBtn")
  })
  

}
