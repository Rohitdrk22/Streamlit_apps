import streamlit as st
import pickle

# Load model
model = pickle.load(open('IMDB_sentiment_analysis.pkl', 'rb'))

# Create title
st.title('Sentiment Analysis Model')

# Text input for review
review = st.text_input('Enter your review:')

# Submit button
submit = st.button('Predict')

# Check if the submit button is clicked and the review text input is not empty
if submit and review.strip() != '':
    prediction = model.predict([review])

    if prediction[0] == 'positive':
        st.success('Positive Review')
    else:
        st.warning('Negative Review')

# Check if the submit button is clicked but the review text input is empty
elif submit and review.strip() == '':
    st.warning('Please enter a review before predicting.')

