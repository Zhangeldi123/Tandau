from rest_framework import serializers
from . import models as model_file

class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type':'password'})
    class Meta:
        model = model_file.Users
        fields = ['email','name','password','password2']
        extra_kwargs ={
            'password':{'write_only':True}
        }
    def validate(self,attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError("Both password should be matched")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return model_file.Users.objects.create_user(**validated_data)

class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=100)
    class Meta:
        model = model_file.Users
        fields = ['email','password']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = model_file.Question_Category
        fields = '__all__'

class QuestionListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name',read_only=True)
    class Meta:
        model = model_file.Questions
        fields = ['id','text','difficulty','category_name']

class ChoicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = model_file.Choices
        fields = ['id','text']  # is_correct (solution) is excluded (not showing) to prevent cheating

class QuestionDetailSerializer(serializers.ModelSerializer):
    choice = ChoicesSerializer(many=True,read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = model_file.Questions
        fields = ['id','text','difficulty','category_name','choice']

class AnswerSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = model_file.UserSolutions
        fields = ['question','selected_answer']

    def validate(self, attrs):
        question = attrs['question']
        selected_answer = attrs['selected_answer']

        if selected_answer.question.id != question.id:
            raise serializers.ValidationError("Your selected answer is not related to this question")
        return attrs

class UserHistorySerializer(serializers.ModelSerializer):
    question_descr = serializers.CharField(source='question.text',read_only=True)
    selected_answer_descr = serializers.CharField(source='selected_answer.text',read_only=True)
    class Meta:
        model = model_file.UserSolutions
        fields = ['question','question_descr','selected_answer_descr','is_correct','answered_at']